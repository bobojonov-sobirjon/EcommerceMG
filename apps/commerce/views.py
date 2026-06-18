from decimal import Decimal

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.async_pagination import paginate

from commerce.models import Manufacturer, ManufacturerFeature, Product, ProductType
from commerce.serializers import (
    CatalogCategorySerializer,
    EngineManufacturerBannerSerializer,
    EngineManufacturerPageSerializer,
    ManufacturerDetailSerializer,
    ManufacturerListSerializer,
    OrderCreateSerializer,
    OrderCreatedSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)

def product_filter(qs, request, *, apply_type=True, apply_manufacturer=True):
    params = request.query_params
    if apply_type and (ptype := params.get('type')):
        qs = qs.filter(product_type=ptype)
    search = (params.get('search') or params.get('name') or '').strip()
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(artikul__icontains=search)
            | Q(description__icontains=search),
        )
    if apply_manufacturer and (mn := params.get('manufacturer')):
        try:
            qs = qs.filter(manufacturer_id=int(mn))
        except ValueError:
            pass
    if mn := params.get('min_price'):
        try:
            qs = qs.filter(price__gte=Decimal(str(mn)))
        except Exception:
            pass
    if mx := params.get('max_price'):
        try:
            qs = qs.filter(price__lte=Decimal(str(mx)))
        except Exception:
            pass
    return qs


def product_price_order(qs, request):
    """Сортировка по цене: order_price=asc | desc."""
    raw = (request.query_params.get('order_price') or '').strip().lower()
    if raw in ('asc', 'price_asc', 'low', 'cheaper'):
        return qs.order_by('price', 'id')
    if raw in ('desc', 'price_desc', 'high', 'expensive'):
        return qs.order_by('-price', '-id')
    return qs.order_by('ordering', '-id')


def _engine_manufacturers_qs():
    return (
        Manufacturer.objects.filter(products__product_type=ProductType.ENGINES)
        .distinct()
        .select_related('seo_record')
        .order_by('ordering', 'id')
    )


def _engine_manufacturer_detail_qs():
    return (
        _engine_manufacturers_qs()
        .prefetch_related(
            Prefetch(
                'features',
                queryset=ManufacturerFeature.objects.order_by('ordering', 'id'),
            ),
        )
    )


def _engine_products_qs(manufacturer_id: int):
    return (
        Product.objects.filter(
            product_type=ProductType.ENGINES,
            manufacturer_id=manufacturer_id,
        )
        .select_related('manufacturer', 'seo_record')
        .prefetch_related('images')
    )


def _paginated_products_payload(request, qs, *, scoped_filters=False):
    page = int(request.query_params.get('page', 1) or 1)
    page_size = int(request.query_params.get('page_size', 20) or 20)
    qs = product_filter(
        qs,
        request,
        apply_type=not scoped_filters,
        apply_manufacturer=not scoped_filters,
    )
    qs = product_price_order(qs, request)
    page_ctx = paginate(qs, page=page, page_size=page_size, max_page_size=100)
    ser = ProductListSerializer(
        page_ctx.results,
        many=True,
        context={'request': request},
    )
    return {
        'count': page_ctx.count,
        'page': page_ctx.page,
        'page_size': page_ctx.page_size,
        'total_pages': page_ctx.total_pages,
        'results': ser.data,
    }


def _engine_manufacturer_page(request, manufacturer: Manufacturer):
    products_payload = _paginated_products_payload(
        request,
        _engine_products_qs(manufacturer.pk),
        scoped_filters=True,
    )
    banner = EngineManufacturerBannerSerializer(
        manufacturer,
        context={'request': request},
    ).data
    return {
        'manufacturer': banner,
        'products': products_payload,
    }


class CatalogCategoriesView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Каталог'],
        summary='Категории каталога',
        description=(
            'Три раздела каталога. Для запчастей и шин — сразу список товаров (`hub=products`). '
            'Для двигателей — сначала производители (`hub=manufacturers`), затем страница производителя с баннером.'
        ),
        responses={200: CatalogCategorySerializer(many=True)},
    )
    def get(self, request):
        data = [
            {
                'type': ProductType.SPARE_PARTS,
                'label': ProductType.SPARE_PARTS.label,
                'hub': 'products',
            },
            {
                'type': ProductType.TIRES,
                'label': ProductType.TIRES.label,
                'hub': 'products',
            },
            {
                'type': ProductType.ENGINES,
                'label': ProductType.ENGINES.label,
                'hub': 'manufacturers',
            },
        ]
        return Response(data)


class EngineManufacturerListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Каталог — двигатели'],
        summary='Производители двигателей',
        description='Список производителей, у которых есть товары категории «Двигатели».',
        responses={200: ManufacturerListSerializer(many=True)},
    )
    def get(self, request):
        rows = list(_engine_manufacturers_qs())
        data = ManufacturerListSerializer(rows, many=True, context={'request': request}).data
        return Response(data)


class EngineManufacturerPageBySlugView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Каталог — двигатели'],
        summary='Страница двигателей производителя (slug)',
        description='Сверху баннер и контент производителя, снизу — двигатели этого производителя с пагинацией.',
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Номер страницы товаров',
                default=1,
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Размер страницы товаров (не больше 100)',
                default=20,
            ),
            OpenApiParameter(
                name='order_price',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Сортировка по цене: asc или desc',
                enum=['asc', 'desc'],
            ),
        ],
        responses={200: EngineManufacturerPageSerializer},
    )
    def get(self, request, slug):
        obj = get_object_or_404(
            _engine_manufacturer_detail_qs(),
            seo_record__slug=slug,
        )
        payload = _engine_manufacturer_page(request, obj)
        return Response(payload)


class EngineManufacturerPageByIdView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Каталог — двигатели'],
        summary='Страница двигателей производителя (id)',
        description='То же, что по slug.',
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                default=1,
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                default=20,
            ),
        ],
        responses={200: EngineManufacturerPageSerializer},
    )
    def get(self, request, pk):
        obj = get_object_or_404(_engine_manufacturer_detail_qs(), pk=pk)
        payload = _engine_manufacturer_page(request, obj)
        return Response(payload)


class ManufacturerListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Производители'],
        summary='Список производителей',
        description='Карточки партнёров для блока «с кем работаем». Только GET.',
        responses={200: ManufacturerListSerializer(many=True)},
    )
    def get(self, request):
        qs = Manufacturer.objects.select_related('seo_record').order_by('ordering', 'id')
        rows = list(qs)
        data = ManufacturerListSerializer(rows, many=True, context={'request': request}).data
        return Response(data)


class ManufacturerDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Производители'],
        summary='Детально по производителю (id)',
        description='Подробное описание бренда (страница партнёра).',
        responses={200: ManufacturerDetailSerializer},
    )
    def get(self, request, pk):
        obj = Manufacturer.objects.select_related('seo_record').get(pk=pk)
        data = ManufacturerDetailSerializer(obj, context={'request': request}).data
        return Response(data)


class ManufacturerDetailBySlugView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Производители'],
        summary='Детально по производителю (slug)',
        description='То же, что по id, но поиск по полю `slug`.',
        responses={200: ManufacturerDetailSerializer},
    )
    def get(self, request, slug):
        obj = Manufacturer.objects.select_related('seo_record').get(seo_record__slug=slug)
        data = ManufacturerDetailSerializer(obj, context={'request': request}).data
        return Response(data)


class ProductListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Каталог — товары'],
        summary='Список товаров с фильтрами',
        description='Фильтры и пагинация через query-string (см. параметры ниже).',
        parameters=[
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Тип товара',
                enum=['spare_parts', 'tires', 'engines'],
            ),
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Поиск по названию, артикулу и описанию (icontains)',
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='То же, что `name`: поиск по названию, артикулу и описанию',
            ),
            OpenApiParameter(
                name='manufacturer',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID производителя',
            ),
            OpenApiParameter(
                name='min_price',
                type=OpenApiTypes.DECIMAL,
                location=OpenApiParameter.QUERY,
                description='Минимальная цена с НДС',
            ),
            OpenApiParameter(
                name='max_price',
                type=OpenApiTypes.DECIMAL,
                location=OpenApiParameter.QUERY,
                description='Максимальная цена с НДС',
            ),
            OpenApiParameter(
                name='order_price',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Сортировка по цене: asc (дешевле) или desc (дороже)',
                enum=['asc', 'desc'],
            ),
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Номер страницы',
                default=1,
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Размер страницы (не больше 100)',
                default=20,
            ),
        ],
        responses={200: ProductListSerializer(many=True)},
    )
    def get(self, request):
        page = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 20) or 20)
        qs = Product.objects.select_related('manufacturer', 'seo_record').prefetch_related('images').all()
        qs = product_filter(qs, request)
        qs = product_price_order(qs, request)
        page_ctx = paginate(qs, page=page, page_size=page_size, max_page_size=100)
        ser = ProductListSerializer(
            page_ctx.results,
            many=True,
            context={'request': request},
        )
        payload = {
            'count': page_ctx.count,
            'page': page_ctx.page,
            'page_size': page_ctx.page_size,
            'total_pages': page_ctx.total_pages,
            'results': ser.data,
        }
        return Response(payload)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Каталог — товары'],
        summary='Товар по id',
        description='Галерея через вложенные `images`. SEO-поля в ответе.',
        responses={200: ProductDetailSerializer},
    )
    def get(self, request, pk):
        obj = Product.objects.select_related('manufacturer', 'seo_record').prefetch_related('images').get(pk=pk)
        data = ProductDetailSerializer(obj, context={'request': request}).data
        return Response(data)


class ProductDetailBySlugView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Каталог — товары'],
        summary='Товар по slug',
        description='То же, что по id, но поиск по полю `slug`.',
        responses={200: ProductDetailSerializer},
    )
    def get(self, request, slug):
        obj = Product.objects.select_related('manufacturer', 'seo_record').prefetch_related('images').get(
            seo_record__slug=slug,
        )
        data = ProductDetailSerializer(obj, context={'request': request}).data
        return Response(data)


class ProductSimilarView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Каталог — товары'],
        summary='Похожие товары (id)',
        description='Те же производитель и тип товара, исключая текущий элемент.',
        responses={200: ProductListSerializer(many=True)},
    )
    def get(self, request, pk):
        anchor = Product.objects.select_related('manufacturer', 'seo_record').prefetch_related('images').get(pk=pk)
        return Response(_similar_products(anchor, request))


class ProductSimilarBySlugView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Каталог — товары'],
        summary='Похожие товары (slug)',
        description='То же, что по id, но якорный товар ищется по `slug`.',
        responses={200: ProductListSerializer(many=True)},
    )
    def get(self, request, slug):
        anchor = Product.objects.select_related('manufacturer', 'seo_record').prefetch_related('images').get(
            seo_record__slug=slug,
        )
        return Response(_similar_products(anchor, request))


def _similar_products(anchor: Product, request):
    qs = Product.objects.exclude(pk=anchor.pk).filter(
        manufacturer_id=anchor.manufacturer_id,
        product_type=anchor.product_type,
    )
    qs = qs.select_related('manufacturer', 'seo_record').prefetch_related('images').order_by('-is_stock', '-id')[:24]
    out = list(qs)
    return ProductListSerializer(out, many=True, context={'request': request}).data


def _persist_order(data):
    ser = OrderCreateSerializer(data=data)
    ser.is_valid(raise_exception=True)
    order = ser.save()
    return OrderCreatedSerializer(order).data


class OrderCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Заказы'],
        summary='Создать заявку / заказ',
        description='Гостевой заказ без аккаунта. Проверяется согласованность сумм с ценами каталога.',
        request=OrderCreateSerializer,
        responses={201: OrderCreatedSerializer},
    )
    def post(self, request):
        payload = _persist_order(dict(request.data))
        return Response(payload, status=status.HTTP_201_CREATED)
