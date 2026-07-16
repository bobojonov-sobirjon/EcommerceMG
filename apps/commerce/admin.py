from decimal import Decimal

from django import forms
from django.contrib import admin, messages
from django.core.files.storage import default_storage
from django.utils.html import format_html

from commerce.models import (
    Manufacturer,
    ManufacturerFeature,
    ManufacturerSeo,
    Order,
    OrderProduct,
    Product,
    ProductImage,
    ProductSeo,
)
from config.admin_seo import SeoTabularInline


def _media_exists(file_field) -> bool:
    if not file_field or not file_field.name:
        return False
    try:
        return default_storage.exists(file_field.name)
    except (OSError, ValueError):
        return False


def _preview_img(url: str, css_class: str = 'admin-image-preview') -> str:
    return format_html('<img src="{}" class="{}" alt="" />', url, css_class)


def _preview_logo(url: str, css_class: str = 'admin-image-preview') -> str:
    return format_html(
        '<img src="{}" class="{}" alt="" style="max-height:120px;object-fit:contain;" />',
        url,
        css_class,
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    classes = ('images-inline',)
    readonly_fields = ('image_preview',)
    fields = ('image_preview', 'image', 'ordering')

    @admin.display(description='Предпросмотр')
    def image_preview(self, obj: ProductImage):
        if obj.pk and _media_exists(obj.image):
            return _preview_img(obj.image.url)
        return '—'


class ProductSeoInline(SeoTabularInline):
    model = ProductSeo


class ManufacturerSeoInline(SeoTabularInline):
    model = ManufacturerSeo


class ManufacturerFeatureInline(admin.TabularInline):
    model = ManufacturerFeature
    extra = 0
    min_num = 0
    fields = ('title', 'description', 'icon', 'ordering')
    ordering = ('ordering', 'id')
    classes = ('features-inline',)
    verbose_name = 'Преимущество'
    verbose_name_plural = 'Преимущества'

    def get_extra(self, request, obj=None, **kwargs):
        if obj is None:
            return 0
        if obj.features.exists():
            return 0
        return 3


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    raw_id_fields = ('product',)
    extra = 0


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_slug', 'ordering', 'logo_thumb', 'updated_at')
    list_display_links = ('name',)
    search_fields = ('name', 'seo_record__slug', 'seo_record__seo_title')
    readonly_fields = ('logo_preview', 'hero_preview')
    inlines = (ManufacturerFeatureInline, ManufacturerSeoInline,)
    fieldsets = (
        (None, {'fields': ('name', 'description', 'ordering')}),
        (
            'Страница двигателей',
            {
                'fields': ('hero_preview', 'hero_image', 'features_heading'),
                'description': (
                    'Баннер и преимущества — для страницы «Двигатели → этот производитель». '
                    'Не путать с разделом «Баннеры» (слайдер на главной). '
                    'Блок «Преимущества» — таблица ниже на этой же странице.'
                ),
            },
        ),
        ('Логотип', {'fields': ('logo_preview', 'logo')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('seo_record')

    @admin.display(description='Slug')
    def display_slug(self, obj: Manufacturer):
        record = getattr(obj, 'seo_record', None)
        return record.slug if record else '—'

    @admin.display(description='Логотип')
    def logo_thumb(self, obj: Manufacturer):
        if _media_exists(obj.logo):
            return _preview_logo(obj.logo.url, 'admin-image-preview--list')
        return '—'

    @admin.display(description='Текущий логотип')
    def logo_preview(self, obj: Manufacturer):
        if obj.pk and _media_exists(obj.logo):
            return _preview_logo(obj.logo.url)
        return '—'

    @admin.display(description='Текущий баннер')
    def hero_preview(self, obj: Manufacturer):
        if obj.pk and _media_exists(obj.hero_image):
            return _preview_img(obj.hero_image.url)
        return '—'


@admin.register(ManufacturerFeature)
class ManufacturerFeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'manufacturer', 'ordering')
    list_filter = ('manufacturer',)
    search_fields = ('title', 'description', 'manufacturer__name')
    autocomplete_fields = ('manufacturer',)
    ordering = ('manufacturer__ordering', 'ordering', 'id')


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price'].required = False
        self.fields['price'].help_text = (
            'Можно оставить пустым, если включено «Цена по запросу».'
        )

    def clean(self):
        cleaned = super().clean()
        on_request = cleaned.get('price_on_request')
        price = cleaned.get('price')
        if on_request:
            cleaned['price'] = Decimal('0')
        elif price is None:
            self.add_error('price', 'Укажите цену или включите «Цена по запросу».')
        return cleaned


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        'thumbnail_list',
        'name',
        'display_slug',
        'artikul',
        'product_type',
        'manufacturer',
        'price',
        'price_on_request',
        'is_stock',
    )
    list_display_links = ('name', 'thumbnail_list')
    list_filter = ('product_type', 'manufacturer', 'is_stock', 'price_on_request')
    search_fields = (
        'name',
        'artikul',
        'description',
        'seo_record__slug',
        'seo_record__seo_title',
    )
    autocomplete_fields = ('manufacturer',)
    inlines = (ProductImageInline, ProductSeoInline)
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'product_type',
                    'manufacturer',
                    'name',
                    'artikul',
                    'description',
                    'price',
                    'price_on_request',
                    'is_stock',
                    'ordering',
                ),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if obj.price_on_request:
            obj.price = Decimal('0')
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('seo_record', 'manufacturer').prefetch_related('images')

    @admin.display(description='Slug')
    def display_slug(self, obj: Product):
        record = getattr(obj, 'seo_record', None)
        return record.slug if record else '—'

    @admin.display(description='Фото')
    def thumbnail_list(self, obj: Product):
        img = None
        cache = getattr(obj, '_prefetched_objects_cache', None)
        if cache and 'images' in cache:
            imgs = sorted(obj.images.all(), key=lambda i: (i.ordering, i.pk))
            first = imgs[0] if imgs else None
            if first and _media_exists(first.image):
                img = first
        else:
            first = obj.images.order_by('ordering', 'pk').first()
            if first and _media_exists(first.image):
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
