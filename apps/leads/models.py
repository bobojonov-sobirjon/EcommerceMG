from django.db import models


class FeedbackMessage(models.Model):
    """Форма «Остались вопросы?»."""

    full_name = models.CharField('Имя', max_length=255)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=64)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Обращение (форма сайта)'
        verbose_name_plural = 'Обращения (форма сайта)'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'{self.full_name} — {self.email}'


class Contact(models.Model):
    """Страница «Контакты»: адрес и email по направлениям (одна запись)."""

    address = models.TextField('Адрес', blank=True)
    email_spare_parts = models.EmailField('Email — запчасти', blank=True)
    email_tires = models.EmailField('Email — шины', blank=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Контакты сайта'
        verbose_name_plural = 'Контакты сайта'

    def __str__(self) -> str:
        return 'Контакты'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class ContactPhone(models.Model):
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='phones',
        verbose_name='Контактный блок',
    )
    phone = models.CharField('Телефон', max_length=64)
    telegram = models.URLField('Telegram', max_length=500, blank=True)
    max_link = models.URLField('Ссылка (MAX)', max_length=500, blank=True)
    label = models.CharField(
        'Подпись (например, запчасти / шины)',
        max_length=255,
        blank=True,
    )
    ordering = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Контактный телефон'
        verbose_name_plural = 'Телефоны'
        ordering = ('ordering', 'id')

    def __str__(self) -> str:
        return self.phone
