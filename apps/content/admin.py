from django.contrib import admin
from django.utils.html import format_html

from content.models import AboutCompany, Banner, News, NewsImage


def _preview_img(url: str, css_class: str = 'admin-image-preview') -> str:
    return format_html(
        '<img src="{}" class="{}" alt="" />',
        url,
        css_class,
    )


class NewsImageInline(admin.TabularInline):
    model = NewsImage
    extra = 0
    readonly_fields = ('image_preview',)
    fields = ('image_preview', 'image', 'ordering')

    @admin.display(description='Предпросмотр')
    def image_preview(self, obj: NewsImage):
        if obj.pk and obj.image and obj.image.name:
            return _preview_img(obj.image.url)
        return '—'


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'banner_thumb', 'ordering', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    ordering = ('ordering', 'id')
    readonly_fields = ('image_preview',)
    fieldsets = (
        (None, {'fields': ('title', 'description', 'ordering', 'is_active')}),
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


@admin.register(AboutCompany)
class AboutCompanyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):  # type: ignore[override]
        return not AboutCompany.objects.exists()


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'news_thumb', 'news_type', 'published_at', 'ordering')
    list_filter = ('news_type',)
    search_fields = ('title',)
    ordering = ('-published_at',)
    date_hierarchy = 'published_at'
    inlines = (NewsImageInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('images')

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
