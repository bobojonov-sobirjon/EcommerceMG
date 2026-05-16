from decimal import Decimal

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.async_pagination import paginate

from commerce.models import Manufacturer, Product
from commerce.serializers import (
    ManufacturerDetailSerializer,
    ManufacturerListSerializer,
    OrderCreateSerializer,
    OrderCreatedSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)

def product_filter(qs, request):
    params = request.query_params
    if ptype := params.get('type'):
        qs = qs.filter(product_type=ptype)
    if name := params.get('name'):
        qs = qs.filter(name__icontains=name.strip())
    if mn := params.get('manufacturer'):
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


class ManufacturerListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Производители'],
        summary='Список производителей',
        description='Карточки партнёров для блока «с кем работаем». Только GET.',
        responses={200: ManufacturerListSerializer(many=True)},
    )
    def get(self, request):
        qs = Manufacturer.objects.order_by('ordering', 'id')
        rows = list(qs)
        data = ManufacturerListSerializer(rows, many=True, context={'request': request}).data
        return Response(data)


class ManufacturerDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Производители'],
        summary='Детально по производителю',
        description='Подробное описание бренда (страница партнёра).',
        responses={200: ManufacturerDetailSerializer},
    )
    def get(self, request, pk):
        obj = Manufacturer.objects.get(pk=pk)
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
                enum=['spare_parts', 'tires'],
            ),
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Поиск по названию (icontains)',
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
        qs = Product.objects.select_related('manufacturer').prefetch_related('images').all()
        qs = qs.order_by('ordering', '-id')
        qs = product_filter(qs, request)
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
        description='Галерея через вложенные `images`.',
        responses={200: ProductDetailSerializer},
    )
    def get(self, request, pk):
        obj = Product.objects.select_related('manufacturer').prefetch_related('images').get(pk=pk)
        data = ProductDetailSerializer(obj, context={'request': request}).data
        return Response(data)


class ProductSimilarView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Каталог — товары'],
        summary='Похожие товары',
        description='Те же производитель и тип товара, исключая текущий элемент.',
        responses={200: ProductListSerializer(many=True)},
    )
    def get(self, request, pk):
        anchor = Product.objects.select_related('manufacturer').prefetch_related('images').get(pk=pk)
        qs = Product.objects.exclude(pk=anchor.pk).filter(
            manufacturer_id=anchor.manufacturer_id,
            product_type=anchor.product_type,
        )
        qs = qs.select_related('manufacturer').prefetch_related('images').order_by('-is_stock', '-id')[:24]
        out = list(qs)
        data = ProductListSerializer(out, many=True, context={'request': request}).data
        return Response(data)


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
