from django.contrib import admin, messages
from django.utils.html import format_html

from commerce.models import Manufacturer, Order, OrderProduct, Product, ProductImage

def _preview_img(url: str, css_class: str = 'admin-image-preview') -> str:
    return format_html(
        '<img src="{}" class="{}" alt="" />',
        url,
        css_class,
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ('image_preview',)
    fields = ('image_preview', 'image', 'ordering')

    @admin.display(description='Предпросмотр')
    def image_preview(self, obj: ProductImage):
        if obj.pk and obj.image and obj.image.name:
            return _preview_img(obj.image.url)
        return '—'


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    raw_id_fields = ('product',)
    extra = 0


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'ordering', 'logo_thumb', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('logo_preview', 'hero_preview')
    fieldsets = (
        (None, {'fields': ('name', 'description', 'ordering')}),
        ('Логотип', {'fields': ('logo_preview', 'logo')}),
        ('Обложка', {'fields': ('hero_preview', 'hero_image')}),
    )

    @admin.display(description='Логотип')
    def logo_thumb(self, obj: Manufacturer):
        if obj.logo and obj.logo.name:
            return _preview_img(obj.logo.url, 'admin-image-preview--list')
        return '—'

    @admin.display(description='Текущий логотип')
    def logo_preview(self, obj: Manufacturer):
        if obj.pk and obj.logo and obj.logo.name:
            return _preview_img(obj.logo.url)
        return '—'

    @admin.display(description='Текущая обложка')
    def hero_preview(self, obj: Manufacturer):
        if obj.pk and obj.hero_image and obj.hero_image.name:
            return _preview_img(obj.hero_image.url)
        return '—'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail_list',
        'name',
        'artikul',
        'product_type',
        'manufacturer',
        'price',
        'is_stock',
    )
    list_filter = ('product_type', 'manufacturer', 'is_stock')
    search_fields = ('name', 'artikul')
    autocomplete_fields = ('manufacturer',)
    inlines = (ProductImageInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('images')

    @admin.display(description='Фото')
    def thumbnail_list(self, obj: Product):
        img = None
        cache = getattr(obj, '_prefetched_objects_cache', None)
        if cache and 'images' in cache:
            imgs = sorted(obj.images.all(), key=lambda i: (i.ordering, i.pk))
            first = imgs[0] if imgs else None
            if first and first.image and first.image.name:
                img = first
        else:
            first = obj.images.order_by('ordering', 'pk').first()
            if first and first.image and first.image.name:
                img = first
        if img:
            return _preview_img(img.image.url, 'admin-image-preview--list')
        return '—'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'new_badge',
        'phone',
        'total_price',
        'is_seen_moderator',
        'created_at',
    )
    list_filter = ('is_seen_moderator',)
    search_fields = ('full_name', 'phone')
    inlines = (OrderProductInline,)
    ordering = ('-created_at',)

    @admin.display(description='')
    def new_badge(self, obj: Order):
        if obj.is_seen_moderator:
            return format_html(
                '<span class="badge bg-warning text-white" title="{}">Новая</span>',
                'Модератор ещё не открывал карточку',
            )
        return format_html(
                '<span class="badge bg-success text-white" title="{}">Просмотрена</span>',
                'Модератор просмотрел карточку',
            ) 

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """При открытии карточки в админке заявка считается просмотренной."""
        if request.method == 'GET':
            updated = Order.objects.filter(pk=object_id, is_seen_moderator=True).update(
                is_seen_moderator=False,
            )
            if updated:
                self.message_user(
                    request,
                    'Заявка отмечена как просмотренная.',
                    level=messages.INFO,
                )
        return super().change_view(request, object_id, form_url, extra_context)