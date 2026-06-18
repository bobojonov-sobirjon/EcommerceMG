from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.async_pagination import paginate

from content.models import AboutCompany, Banner, Certification, News
from content.serializers import (
    AboutCompanySerializer,
    BannerSerializer,
    CertificationSerializer,
    NewsDetailSerializer,
    NewsListSerializer,
)


class BannerListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Главная — баннеры'],
        summary='Активные баннеры',
        description='Слайдер главной страницы. Фильтр по полю `type` (без учёта регистра). Только чтение.',
        parameters=[
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Тип / акцент слайда (например: НАДЕЖНОСТЬ, КАЧЕСТВО)',
            ),
        ],
        responses={200: BannerSerializer(many=True)},
    )
    def get(self, request):
        qs = Banner.objects.filter(is_active=True).order_by('ordering', 'id')
        if banner_type := request.query_params.get('type', '').strip():
            qs = qs.filter(type__iexact=banner_type)
        banners = list(qs)
        ser = BannerSerializer(banners, many=True, context={'request': request})
        return Response(ser.data)


class CertificationListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Сертификаты'],
        summary='Список сертификатов',
        description='Блок «Наши сертификаты»: название, превью, ссылка на PDF и размер файла. Только GET.',
        responses={200: CertificationSerializer(many=True)},
    )
    def get(self, request):
        qs = Certification.objects.order_by('-created_at', '-id')
        rows = list(qs)
        ser = CertificationSerializer(rows, many=True, context={'request': request})
        return Response(ser.data)


class AboutCompanyView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Компания'],
        summary='Страница «О компании»',
        description='Singleton: одна карточка с метриками (как в макете).',
        responses={200: AboutCompanySerializer},
    )
    def get(self, request):
        obj, _created = AboutCompany.objects.select_related('seo_record').get_or_create(pk=1)
        data = AboutCompanySerializer(obj).data
        return Response(data)


class NewsListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Новости'],
        summary='Лента новостей',
        description=(
            'Фильтр по типу (`news_type` или `type`). Пагинация: `page`, `page_size` (макс. 80).'
        ),
        parameters=[
            OpenApiParameter(
                name='news_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Тип новости',
                enum=['useful', 'company'],
            ),
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='То же, что `news_type` (альтернативное имя)',
                enum=['useful', 'company'],
            ),
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Номер страницы (с 1)',
                default=1,
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Размер страницы (не больше 80)',
                default=12,
            ),
        ],
        responses={200: NewsListSerializer(many=True)},
    )
    def get(self, request):
        page = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 12) or 12)
        qs = News.objects.select_related('seo_record').prefetch_related('images').order_by('-published_at', '-id')
        nt = request.query_params.get('type') or request.query_params.get('news_type')
        if nt:
            qs = qs.filter(news_type=nt)
        page_ctx = paginate(qs, page=page, page_size=page_size, max_page_size=80)
        ser = NewsListSerializer(page_ctx.results, many=True, context={'request': request})
        return Response(
            {
                'count': page_ctx.count,
                'page': page_ctx.page,
                'page_size': page_ctx.page_size,
                'total_pages': page_ctx.total_pages,
                'results': ser.data,
            },
        )


class NewsDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Новости'],
        summary='Детальная страница новости (id)',
        description='Подробный текст, галерея `images` и SEO-поля.',
        responses={200: NewsDetailSerializer},
    )
    def get(self, request, pk):
        obj = News.objects.select_related('seo_record').prefetch_related('images').get(pk=pk)
        ser = NewsDetailSerializer(obj, context={'request': request})
        return Response(ser.data)


class NewsDetailBySlugView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Новости'],
        summary='Детальная страница новости (slug)',
        description='То же, что по id, но поиск по полю `slug`.',
        responses={200: NewsDetailSerializer},
    )
    def get(self, request, slug):
        obj = News.objects.select_related('seo_record').prefetch_related('images').get(seo_record__slug=slug)
        ser = NewsDetailSerializer(obj, context={'request': request})
        return Response(ser.data)
