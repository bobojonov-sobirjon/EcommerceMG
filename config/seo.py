"""Общие утилиты и модели для SEO."""

from django.db import models
from django.utils.text import slugify

SEO_TITLE_MAX = 255
SEO_DESCRIPTION_MAX = 500


def build_unique_slug(instance, source: str, *, max_length: int = 255) -> str:
    Model = type(instance)
    raw = slugify(str(source).strip(), allow_unicode=True)
    base = raw[:max_length].strip('-')
    if not base:
        base = f'item-{instance.pk or 0}'
    candidate = base
    suffix = 1
    qs = Model.objects.all()
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(slug=candidate).exists():
        tail = f'-{suffix}'
        candidate = f'{base[: max_length - len(tail)]}{tail}'
        suffix += 1
    return candidate


class SeoRecord(models.Model):
    """SEO-запись (inline в админке, OneToOne к родителю)."""

    seo_title = models.CharField(
        'SEO заголовок',
        max_length=SEO_TITLE_MAX,
        blank=True,
        help_text='Заголовок для <title> и поисковиков. Если пусто — подставляется название на сайте.',
    )
    seo_description = models.TextField(
        'SEO описание',
        blank=True,
        max_length=SEO_DESCRIPTION_MAX,
        help_text='Meta description для поисковиков (до 500 символов).',
    )
    slug = models.SlugField(
        'URL (slug)',
        max_length=255,
        unique=True,
        blank=True,
        help_text='Часть адреса страницы. Если пусто — создаётся автоматически.',
    )

    class Meta:
        abstract = True

    def slug_source(self) -> str:
        raise NotImplementedError

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.slug_source())
        super().save(*args, **kwargs)


class PageSeoRecord(models.Model):
    """SEO без slug (одностраничные блоки)."""

    seo_title = models.CharField(
        'SEO заголовок',
        max_length=SEO_TITLE_MAX,
        blank=True,
        help_text='Заголовок для <title>. Если пусто — подставляется на фронтенде.',
    )
    seo_description = models.TextField(
        'SEO описание',
        blank=True,
        max_length=SEO_DESCRIPTION_MAX,
        help_text='Meta description (до 500 символов).',
    )

    class Meta:
        abstract = True
