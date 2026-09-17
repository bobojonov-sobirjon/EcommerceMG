"""Выгрузка товаров в Excel (.xlsx) или CSV для клиента."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count

from commerce.models import Product, ProductType


HEADERS = [
    'ID',
    'Артикул',
    'Наименование',
    'Тип товара (код)',
    'Тип товара',
    'Производитель',
    'Цена с НДС',
    'Цена по запросу',
    'В наличии',
    'Slug',
    'SEO заголовок',
    'SEO описание',
    'Описание',
    'Порядок',
    'Кол-во фото',
    'Создано',
]


def _product_rows(qs):
    for p in qs.iterator(chunk_size=500):
        seo = getattr(p, 'seo_record', None)
        yield [
            p.pk,
            p.artikul,
            p.name,
            p.product_type,
            p.get_product_type_display(),
            p.manufacturer.name if p.manufacturer_id else '',
            '' if p.price_on_request else str(p.price),
            'да' if p.price_on_request else 'нет',
            'да' if p.is_stock else 'нет',
            seo.slug if seo else '',
            seo.seo_title if seo else '',
            seo.seo_description if seo else '',
            p.description or '',
            p.ordering,
            getattr(p, 'images_count', 0) or 0,
            p.created_at.strftime('%Y-%m-%d %H:%M') if p.created_at else '',
        ]


class Command(BaseCommand):
    help = 'Выгружает товары в файл .xlsx (Excel) или .csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=('xlsx', 'csv'),
            default='xlsx',
            help='Формат файла (по умолчанию xlsx)',
        )
        parser.add_argument(
            '--type',
            choices=[c[0] for c in ProductType.choices],
            default=None,
            help='Фильтр по типу: spare_parts | tires | engines',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='',
            help='Путь к файлу (по умолчанию media/exports/...)',
        )

    def handle(self, *args, **options):
        fmt: str = options['format']
        ptype = options['type']
        output = (options['output'] or '').strip()

        qs = (
            Product.objects.select_related('manufacturer', 'seo_record')
            .annotate(images_count=Count('images'))
            .order_by('product_type', 'manufacturer__name', 'artikul', 'id')
        )
        if ptype:
            qs = qs.filter(product_type=ptype)

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('Товаров не найдено.'))
            return

        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        type_part = ptype or 'all'
        if not output:
            export_dir = Path(settings.MEDIA_ROOT) / 'exports'
            export_dir.mkdir(parents=True, exist_ok=True)
            output = str(export_dir / f'products_{type_part}_{stamp}.{fmt}')

        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)

        rows = list(_product_rows(qs))

        if fmt == 'xlsx':
            self._write_xlsx(path, rows)
        else:
            self._write_csv(path, rows)

        self.stdout.write(self.style.SUCCESS(f'Готово: {total} товаров -> {path.resolve()}'))

    def _write_csv(self, path: Path, rows: list) -> None:
        with path.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(HEADERS)
            writer.writerows(rows)

    def _write_xlsx(self, path: Path, rows: list) -> None:
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font
        except ImportError:
            self.stdout.write(
                self.style.WARNING('openpyxl не установлен — сохраняю CSV. pip install openpyxl'),
            )
            csv_path = path.with_suffix('.csv')
            self._write_csv(csv_path, rows)
            self.stdout.write(self.style.SUCCESS(f'CSV: {csv_path.resolve()}'))
            raise SystemExit(0)

        wb = Workbook()
        ws = wb.active
        ws.title = 'Товары'
        ws.append(HEADERS)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for row in rows:
            ws.append(row)

        widths = {
            'A': 8,
            'B': 14,
            'C': 48,
            'D': 14,
            'E': 22,
            'F': 18,
            'G': 14,
            'H': 14,
            'I': 12,
            'J': 28,
            'K': 28,
            'L': 36,
            'M': 40,
            'N': 10,
            'O': 12,
            'P': 18,
        }
        for col, width in widths.items():
            ws.column_dimensions[col].width = width

        wb.save(path)
