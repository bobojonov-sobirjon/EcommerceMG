from django.db import models


class Banner(models.Model):
    """Баннер слайдера на главной."""

    title = models.CharField('Заголовок', max_length=255)
    type = models.CharField(
        'Тип (акцент на слайде)',
        max_length=128,
        blank=True,
        help_text='Например: НАДЕЖНОСТЬ — крупная подпись на фоне слайда',
    )
    description = models.TextField('Описание', blank=True)
    image = models.ImageField('Изображение', upload_to='banners/%Y/%m/')
    ordering = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'
        ordering = ('ordering', 'id')

    def __str__(self) -> str:
        return self.title


class AboutCompany(models.Model):
    """Страница «О компании» (единственная запись)."""

    description = models.TextField('Текст о компании', blank=True)
    years_stable = models.CharField('Лет стабильной работы', max_length=32, blank=True)
    satisfied_clients = models.CharField('Довольных клиентов', max_length=32, blank=True)
    parts_in_stock = models.CharField('Запчастей в наличии', max_length=32, blank=True)
    world_brands = models.CharField('Мировых брендов', max_length=32, blank=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'О компании'
        verbose_name_plural = 'О компании'

    def __str__(self) -> str:
        return 'Информация о компании'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass


class NewsType(models.TextChoices):
    USEFUL = 'useful', 'Полезное'
    COMPANY = 'company', 'Новости компании'


class News(models.Model):
    title = models.CharField('Заголовок', max_length=512)
    news_type = models.CharField(
        'Тип',
        max_length=32,
        choices=NewsType.choices,
        db_index=True,
    )
    description = models.TextField('Текст (детально)', blank=True)
    published_at = models.DateField('Дата', db_index=True)
    ordering = models.PositiveSmallIntegerField('Порядок', default=0, db_index=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ('-published_at', '-id')

    def __str__(self) -> str:
        return self.title


class NewsImage(models.Model):
    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Новость',
    )
    image = models.ImageField('Изображение', upload_to='news/%Y/%m/')
    ordering = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Изображение новости'
        verbose_name_plural = 'Изображения новостей'
        ordering = ('ordering', 'id')

    def __str__(self) -> str:
        return f'Изображение к новости {self.news_id}'


class Certification(models.Model):
    """Сертификат для блока «Наши сертификаты»."""

    name = models.CharField('Название', max_length=512)
    thumbnail_image = models.ImageField('Превью', upload_to='certificates/thumbs/%Y/%m/')
    pdf = models.FileField('PDF', upload_to='certificates/pdf/%Y/%m/')
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Сертификат'
        verbose_name_plural = 'Сертификаты'
        ordering = ('-created_at', '-id')

    def __str__(self) -> str:
        return self.name
