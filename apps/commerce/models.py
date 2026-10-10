import logging
from decimal import Decimal
from pathlib import Path

from django.core.validators import MinValueValidator
from django.db import models

from commerce.validators import validate_manufacturer_logo
from config.seo import SeoRecord

logger = logging.getLogger(__name__)


class Manufacturer(models.Model):
    """Производитель / партнёр (блок «с кем работаем» и карточка бренда)."""

    name = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    logo = models.FileField(
        'Логотип (карточка)',
        upload_to='manufacturers/logos/%Y/%m/',
        validators=[validate_manufacturer_logo],
        help_text='JPG, PNG, WebP, GIF или SVG.',
    )
    hero_image = models.ImageField(
        'Баннер (страница двигателей)',
        upload_to='manufacturers/hero/%Y/%m/',
        blank=True,
        null=True,
        help_text='Верхний баннер на странице двигателей этого производителя.',
    )
    features_heading = models.CharField(
        'Заголовок блока преимуществ',
        max_length=255,
        blank=True,
        help_text='Например: «Особенности двигателей Caterpillar». Только для страницы двигателей.',
    )
    ordering = models.PositiveSmallIntegerField('Порядок', default=0, db_index=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'
        ordering = ('ordering', 'id')

    def __str__(self) -> str:
        return self.name


class ManufacturerSeo(SeoRecord):
    manufacturer = models.OneToOneField(
        Manufacturer,
        on_delete=models.CASCADE,
        related_name='seo_record',
        verbose_name='Производитель',
    )

    class Meta:
        verbose_name = 'SEO производителя'
        verbose_name_plural = 'SEO'

    def slug_source(self) -> str:
        return self.manufacturer.name

    def __str__(self) -> str:
        return f'SEO — {self.manufacturer.name}'


class ManufacturerFeature(models.Model):
    """Блок преимуществ на странице двигателей производителя (как в макете Figma)."""

    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.CASCADE,
        related_name='features',
        verbose_name='Производитель',
    )
    title = models.CharField('Заголовок', max_length=255)
    description = models.TextField('Описание', blank=True)
    icon = models.ImageField(
        'Иконка',
        upload_to='manufacturers/features/%Y/%m/',
        blank=True,
        null=True,
    )
    ordering = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Преимущество производителя'
        verbose_name_plural = 'Преимущества производителя'
        ordering = ('ordering', 'id')

    def __str__(self) -> str:
        return self.title


class ProductType(models.TextChoices):
    SPARE_PARTS = 'spare_parts', 'Запчасти'
    TIRES = 'tires', 'Шины для спецтехники'
    ENGINES = 'engines', 'Двигатели'


class Product(models.Model):
    """Товар: запчасти, шины или двигатели."""

    product_type = models.CharField(
        'Тип товара',
        max_length=32,
        choices=ProductType.choices,
        db_index=True,
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='Производитель',
    )
    name = models.CharField('Наименование', max_length=512)
    artikul = models.CharField(
        'Артикул',
        max_length=128,
        db_index=True,
        blank=True,
        default='',
        help_text='Обязателен для запчастей и двигателей, для шин — необязателен.',
    )
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField(
        'Цена с НДС',
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    price_on_request = models.BooleanField(
        'Цена по запросу',
        default=False,
        db_index=True,
        help_text='Если включено — на сайте показывается «Цена по запросу», а не сумма.',
    )
    is_stock = models.BooleanField('В наличии', default=True, db_index=True)
    ordering = models.PositiveSmallIntegerField('Порядок', default=0, db_index=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ('ordering', '-id')
        indexes = [
            models.Index(fields=('product_type', 'manufacturer', 'price')),
        ]

    def __str__(self) -> str:
        return self.name


class ProductSeo(SeoRecord):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='seo_record',
        verbose_name='Товар',
    )

    class Meta:
        verbose_name = 'SEO товара'
        verbose_name_plural = 'SEO'

    def slug_source(self) -> str:
        return '-'.join(part for part in (self.product.name, self.product.artikul) if part)

    def __str__(self) -> str:
        return f'SEO — {self.product.name}'


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Товар',
    )
    image = models.ImageField('Изображение', upload_to='products/%Y/%m/')
    thumbnail = models.ImageField(
        'Превью (webp)',
        upload_to='products/thumbs/%Y/%m/',
        blank=True,
        editable=False,
    )
    ordering = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товара'
        ordering = ('ordering', 'id')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loaded_image_name = self.image.name if self.image else ''

    def __str__(self) -> str:
        return f'#{self.pk} для {self.product_id}'

    def save(self, *args, **kwargs):
        image_changed = bool(self.image) and self.image.name != self._loaded_image_name
        super().save(*args, **kwargs)
        if self.image and (image_changed or not self.thumbnail):
            self.regenerate_thumbnail()

    def regenerate_thumbnail(self) -> bool:
        from commerce.thumbnails import build_webp_thumbnail

        content = build_webp_thumbnail(self.image)
        if content is None:
            return False
        old_name = self.thumbnail.name if self.thumbnail else ''
        try:
            self.thumbnail.save(f'{Path(self.image.name).stem}.webp', content, save=False)
        except OSError as exc:
            logger.warning('Не удалось сохранить превью для изображения #%s: %s', self.pk, exc)
            return False
        type(self).objects.filter(pk=self.pk).update(thumbnail=self.thumbnail.name)
        if old_name and old_name != self.thumbnail.name:
            try:
                self.thumbnail.storage.delete(old_name)
            except OSError:
                pass
        self._loaded_image_name = self.image.name
        return True


class Order(models.Model):
    """Заявка без регистрации пользователя."""

    full_name = models.CharField('ФИО / имя', max_length=255)
    phone = models.CharField('Телефон', max_length=32)
    total_price = models.DecimalField(
        'Итого',
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    # True — модератор ещё не открывал заявку (показывать в уведомлениях). False — просмотрено.
    is_seen_moderator = models.BooleanField(
        'Новая заявка для модератора',
        default=True,
        db_index=True,
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Заявка {self.pk} — {self.full_name}'


class OrderProduct(models.Model):
    """Позиция в заказе: товар, количество и сумма строки (передаются с клиента)."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_lines',
        verbose_name='Товар',
    )
    quantity = models.PositiveIntegerField('Кол-во', validators=[MinValueValidator(1)])
    total_price = models.DecimalField(
        'Сумма строки с НДС',
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    price_on_request = models.BooleanField(
        'Цена по запросу',
        default=False,
        help_text='Товар был «по запросу» на момент заказа — стоимость нужно уточнить у клиента.',
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self) -> str:
        return f'{self.product_id} × {self.quantity}'
