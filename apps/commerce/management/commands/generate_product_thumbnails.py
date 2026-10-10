"""Создаёт webp-превью (~400px) для уже загруженных фото товаров."""
from __future__ import annotations

from django.core.management.base import BaseCommand

from commerce.models import ProductImage


class Command(BaseCommand):
    help = 'Генерирует уменьшенные превью (webp) для фото товаров, у которых их ещё нет.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пересоздать превью и для фото, у которых оно уже есть',
        )

    def handle(self, *args, **options):
        qs = ProductImage.objects.order_by('pk')
        if not options['force']:
            qs = qs.filter(thumbnail='')

        total = qs.count()
        self.stdout.write(f'Фото для обработки: {total}')
        done = failed = 0
        for image in qs.iterator(chunk_size=200):
            if image.regenerate_thumbnail():
                done += 1
            else:
                failed += 1
                self.stdout.write(self.style.WARNING(f'  пропущено фото #{image.pk} ({image.image.name})'))
            if (done + failed) % 100 == 0:
                self.stdout.write(f'  обработано {done + failed}/{total}')

        self.stdout.write(self.style.SUCCESS(f'Готово: создано {done}, пропущено {failed}.'))
