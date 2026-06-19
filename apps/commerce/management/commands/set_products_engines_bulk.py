"""Массово: тип «Двигатели» + «Цена по запросу» для диапазона id товаров."""
from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from commerce.models import Product, ProductType


class Command(BaseCommand):
    help = (
        'Переводит товары в категорию «Двигатели» и ставит «Цена по запросу» '
        '(price_on_request=True, price=0). По умолчанию id 52–352.'
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

        qs = Product.objects.filter(pk__gte=from_id, pk__lte=to_id).order_by('pk')
        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING(f'Товаров с id {from_id}–{to_id} не найдено.'))
            return

        already = qs.filter(
            product_type=ProductType.ENGINES,
            price_on_request=True,
            price=Decimal('0'),
        ).count()

        self.stdout.write(f'Диапазон id: {from_id}–{to_id}')
        self.stdout.write(f'Найдено товаров: {total}')
        self.stdout.write(f'Уже в нужном состоянии: {already}')
        self.stdout.write(f'Будет обновлено: {total - already}')

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
            updated = qs.update(
                product_type=ProductType.ENGINES,
                price_on_request=True,
                price=Decimal('0'),
            )

        self.stdout.write(self.style.SUCCESS(f'Готово. Обновлено записей: {updated}'))
