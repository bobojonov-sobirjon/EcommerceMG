"""Массово вернуть товары в категорию «Запчасти» (откат после set_products_engines_bulk)."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from commerce.models import Product, ProductType


class Command(BaseCommand):
    help = (
        'Возвращает товары в категорию «Запчасти». '
        'По умолчанию id 52–352, только те, что сейчас «Двигатели».'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-id',
            type=int,
            default=52,
            help='Начальный id товара (включительно). По умолчанию: 52',
        )
        parser.add_argument(
            '--to-id',
            type=int,
            default=352,
            help='Конечный id товара (включительно). По умолчанию: 352',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать, что будет изменено, без записи в БД',
        )

    def handle(self, *args, **options):
        from_id: int = options['from_id']
        to_id: int = options['to_id']
        dry_run: bool = options['dry_run']

        if from_id > to_id:
            self.stderr.write(self.style.ERROR('--from-id не может быть больше --to-id'))
            return

        qs = Product.objects.filter(
            pk__gte=from_id,
            pk__lte=to_id,
            product_type=ProductType.ENGINES,
        ).order_by('pk')
        total = qs.count()
        if total == 0:
            self.stdout.write(
                self.style.WARNING(
                    f'В диапазоне id {from_id}–{to_id} нет товаров типа «Двигатели».',
                ),
            )
            return

        self.stdout.write(f'Диапазон id: {from_id}–{to_id}')
        self.stdout.write(f'Будет возвращено в «Запчасти»: {total}')

        sample = list(qs.values_list('pk', 'artikul', 'name', 'product_type')[:5])
        if sample:
            self.stdout.write('Первые записи:')
            for pk, art, name, ptype in sample:
                self.stdout.write(f'  #{pk} [{art}] {name[:60]} (сейчас: {ptype})')

        if total > 5:
            tail = list(
                qs.order_by('-pk').values_list('pk', 'artikul', 'name', 'product_type')[:3],
            )
            tail.reverse()
            self.stdout.write('Последние записи:')
            for pk, art, name, ptype in tail:
                self.stdout.write(f'  #{pk} [{art}] {name[:60]} (сейчас: {ptype})')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN: изменения не сохранены.'))
            return

        with transaction.atomic():
            updated = qs.update(product_type=ProductType.SPARE_PARTS)

        self.stdout.write(self.style.SUCCESS(f'Готово. Обновлено записей: {updated}'))
