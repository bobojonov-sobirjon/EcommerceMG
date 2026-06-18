from django.contrib import admin
from django.utils.html import format_html

from config.admin_seo import PageSeoTabularInline, SeoTabularInline
from content.models import (
    AboutCompany,
    AboutCompanySeo,
    Banner,
    Certification,
    News,
    NewsImage,
    NewsSeo,
)


def _preview_img(url: str, css_class: str = 'admin-image-preview') -> str:
    return format_html('<img src="{}" class="{}" alt="" />', url, css_class)


class NewsImageInline(admin.TabularInline):
    model = NewsImage
    extra = 0
    classes = ('images-inline',)
    readonly_fields = ('image_preview',)
    fields = ('image_preview', 'image', 'ordering')

    @admin.display(description='Предпросмотр')
    def image_preview(self, obj: NewsImage):
        if obj.pk and obj.image and obj.image.name:
            return _preview_img(obj.image.url)
        return '—'


class NewsSeoInline(SeoTabularInline):
    model = NewsSeo


class AboutCompanySeoInline(PageSeoTabularInline):
    model = AboutCompanySeo


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'banner_thumb', 'ordering', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'type')
    ordering = ('ordering', 'id')
    readonly_fields = ('image_preview',)
    fieldsets = (
        (
            None,
            {
                'fields': ('title', 'type', 'description', 'ordering', 'is_active'),
                'description': (
                    'Слайдер на главной странице сайта. '
                    'Баннеры страниц двигателей (Cummins, Caterpillar и т.д.) '
                    'настраиваются в разделе «Каталог → Производители».'
                ),
            },
        ),
        ('Изображение', {'fields': ('image_preview', 'image')}),
    )

    @admin.display(description='Изображение')
    def banner_thumb(self, obj: Banner):
        if obj.image and obj.image.name:
            return _preview_img(obj.image.url, 'admin-image-preview--list')
        return '—'

    @admin.display(description='Текущее изображение')
    def image_preview(self, obj: Banner):
        if obj.pk and obj.image and obj.image.name:
            return _preview_img(obj.image.url)
        return '—'


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'cert_thumb', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
    readonly_fields = ('thumb_preview', 'created_at')
    fieldsets = (
        (None, {'fields': ('name', 'created_at')}),
        ('Файлы', {'fields': ('thumb_preview', 'thumbnail_image', 'pdf')}),
    )

    @admin.display(description='Превью')
    def cert_thumb(self, obj: Certification):
        if obj.thumbnail_image and obj.thumbnail_image.name:
            return _preview_img(obj.thumbnail_image.url, 'admin-image-preview--list')
        return '—'

    @admin.display(description='Превью')
    def thumb_preview(self, obj: Certification):
        if obj.pk and obj.thumbnail_image and obj.thumbnail_image.name:
            return _preview_img(obj.thumbnail_image.url)
        return '—'


@admin.register(AboutCompany)
class AboutCompanyAdmin(admin.ModelAdmin):
    inlines = (AboutCompanySeoInline,)
    fieldsets = (
        (None, {'fields': ('description',)}),
        (
            'Метрики',
            {
                'fields': (
                    'years_stable',
                    'satisfied_clients',
                    'parts_in_stock',
                    'world_brands',
                ),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('seo_record')

    def has_add_permission(self, request):  # type: ignore[override]
        return not AboutCompany.objects.exists()


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_slug', 'news_thumb', 'news_type', 'published_at', 'ordering')
    list_display_links = ('title',)
    list_filter = ('news_type',)
    search_fields = ('title', 'seo_record__slug', 'seo_record__seo_title')
    ordering = ('-published_at',)
    date_hierarchy = 'published_at'
    inlines = (NewsImageInline, NewsSeoInline)
    fieldsets = (
        (None, {'fields': ('title', 'news_type', 'description', 'published_at', 'ordering')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('seo_record').prefetch_related('images')

    @admin.display(description='Slug')
    def display_slug(self, obj: News):
        record = getattr(obj, 'seo_record', None)
        return record.slug if record else '—'

    @admin.display(description='Фото')
    def news_thumb(self, obj: News):
        img = None
        cache = getattr(obj, '_prefetched_objects_cache', None)
        if cache and 'images' in cache:
            imgs = sorted(obj.images.all(), key=lambda i: (i.ordering, i.pk))
            f = imgs[0] if imgs else None
            if f and f.image and f.image.name:
                img = f
        else:
            f = obj.images.order_by('ordering', 'pk').first()
            if f and f.image and f.image.name:
                img = f
        if img:
            return _preview_img(img.image.url, 'admin-image-preview--list')
        return '—'
