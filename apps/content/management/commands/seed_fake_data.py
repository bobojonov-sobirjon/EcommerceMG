"""Заполнение демо-данными всех моделей проекта (RU, близко к макетам)."""
from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from commerce.models import (
    Manufacturer,
    ManufacturerFeature,
    ManufacturerSeo,
    Order,
    OrderProduct,
    Product,
    ProductImage,
    ProductSeo,
    ProductType,
)
from content.models import AboutCompany, Banner, Certification, News, NewsImage, NewsType
from leads.models import Contact, ContactPhone, FeedbackMessage

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise RuntimeError('Требуется Pillow: pip install pillow') from exc


def _jpg_bytes(width: int, height: int, hue: tuple[int, int, int]) -> bytes:
    img = Image.new('RGB', (width, height), color=hue)
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return buf.getvalue()


def fake_image(filename: str, width: int = 640, height: int = 400, seed: int = 0) -> ContentFile:
    r = 40 + (seed * 37) % 160
    g = 50 + (seed * 19) % 180
    b = 60 + (seed * 53) % 170
    return ContentFile(_jpg_bytes(width, height, (r, g, b)), name=filename)


def _file_missing(file_field) -> bool:
    if not file_field or not file_field.name:
        return True
    try:
        return not file_field.storage.exists(file_field.name)
    except (OSError, ValueError):
        return True


def _ensure_product_images(product: Product, pid: int, count: int = 2) -> None:
    images = list(product.images.order_by('ordering', 'pk'))
    if images and not any(_file_missing(img.image) for img in images):
        return
    for img in images:
        img.delete()
    for o in range(count):
        img = ProductImage(product=product, ordering=o)
        img.image.save(
            f'prod_{product.pk}_{o}.jpg',
            fake_image(f'p{product.pk}_{o}.jpg', 500, 500, pid + o),
            save=True,
        )


def fake_pdf(filename: str, size_kb: int = 780) -> ContentFile:
    """Минимальный PDF для демо (размер ~size_kb для отображения pdf_size_mb)."""
    header = (
        b'%PDF-1.4\n'
        b'1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
        b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
        b'3 0 obj<</Type/Page/MediaBox[0 0 400 560]/Parent 2 0 R>>endobj\n'
        b'xref\n0 4\n'
        b'trailer<</Size 4/Root 1 0 R>>\n'
        b'startxref\n9\n%%EOF\n'
    )
    target = max(len(header), size_kb * 1024)
    body = header + b'% demo padding\n' + (b'0' * (target - len(header) - 16))
    return ContentFile(body, name=filename        )


def _manufacturer_file_slug(name: str) -> str:
    return name.lower().replace(' ', '_').replace('-', '_')


def _ensure_manufacturer_seo(manufacturer: Manufacturer) -> None:
    record, _ = ManufacturerSeo.objects.get_or_create(manufacturer=manufacturer)
    if not record.slug:
        record.save()


def _ensure_product_seo(product: Product) -> None:
    record, _ = ProductSeo.objects.get_or_create(product=product)
    if not record.slug:
        record.save()


class Command(BaseCommand):
    help = 'Создаёт демонстрационные записи для всех моделей API (баннеры, контакты, каталог, заказы и т.д.).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить ранее сгенерированные записи (кроме структуры singleton через пересоздание)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear()

        with transaction.atomic():
            self._seed_about()
            self._seed_contact()
            self._seed_manufacturers_and_products()
            self._seed_banners()
            self._seed_certifications()
            self._seed_news()
            self._seed_feedback()
            self._seed_orders()

        self.stdout.write(self.style.SUCCESS('Готово: демо-данные созданы.'))

    def _clear(self) -> None:
        OrderProduct.objects.all().delete()
        Order.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        Manufacturer.objects.all().delete()
        NewsImage.objects.all().delete()
        News.objects.all().delete()
        Banner.objects.all().delete()
        Certification.objects.all().delete()
        FeedbackMessage.objects.all().delete()
        ContactPhone.objects.all().delete()
        Contact.objects.all().delete()
        AboutCompany.objects.all().delete()
        self.stdout.write(self.style.WARNING('Таблицы контента/каталога/обращений очищены.'))

    def _seed_about(self) -> None:
        AboutCompany.objects.update_or_create(
            pk=1,
            defaults={
                'description': (
                    'ООО «МАКСАН ГРУПП» — надёжный партнёр в поставках оборудования и запчастей '
                    'для горнодобывающей отрасли. Работаем с ведущими мировыми производителями: '
                    'CATERPILLAR, ATLAS COPCO, EPIROC, SANDVIK, CUMMINS, DEUTZ, ALLISON, DANA, KESSLER.'
                ),
                'years_stable': '10+',
                'satisfied_clients': '1 000+',
                'parts_in_stock': '5 000+',
                'world_brands': '10',
            },
        )

    def _seed_contact(self) -> None:
        contact, _ = Contact.objects.get_or_create(
            pk=1,
            defaults={
                'address': 'г. Санкт-Петербург, Невский пр-т, д. 30, офисы 5.4 и 6.5',
                'email_spare_parts': 'info@maksan-group.ru',
                'email_tires': 'andrey.ivanov@maksan-group.ru',
            },
        )
        if not contact.address:
            contact.address = 'г. Санкт-Петербург, Невский пр-т, д. 30, офисы 5.4 и 6.5'
            contact.email_spare_parts = 'info@maksan-group.ru'
            contact.email_tires = 'andrey.ivanov@maksan-group.ru'
            contact.save()

        if not contact.phones.exists():
            ContactPhone.objects.create(
                contact=contact,
                phone='+7 (921) 905-70-21',
                telegram='https://t.me/example_spare_parts',
                max_link='https://max.example/spare',
                label='Запчасти для спецтехники',
                ordering=0,
            )
            ContactPhone.objects.create(
                contact=contact,
                phone='+7 (921) 306-51-25',
                telegram='https://t.me/example_tires',
                max_link='https://max.example/tires',
                label='Шины для спецтехники',
                ordering=1,
            )

    def _seed_manufacturers_and_products(self) -> None:
        # 8 производителей двигателей по макетам Figma
        engine_specs = [
            (
                'Caterpillar',
                0,
                'Оригинальные дизельные двигатели Caterpillar для спецтехники, карьерной и дорожно-строительной техники.',
            ),
            (
                'Cummins',
                1,
                'Надёжные дизельные двигатели Cummins для спецтехники с гарантией и быстрой поставкой.',
            ),
            (
                'Deutz',
                2,
                'Силовые агрегаты Deutz для промышленной, строительной и сельскохозяйственной техники.',
            ),
            (
                'Weichai',
                3,
                'Промышленные двигатели Weichai для спецтехники и энергетического оборудования.',
            ),
            (
                'Komatsu',
                4,
                'Двигатели Komatsu для экскаваторов, погрузчиков и карьерной техники.',
            ),
            (
                'MTU',
                5,
                'Дизельные и газовые двигатели MTU для генераторов и тяжёлой спецтехники.',
            ),
            (
                'Perkins',
                6,
                'Двигатели Perkins для строительной, сельскохозяйственной и промышленной техники.',
            ),
            (
                'Volvo Penta',
                7,
                'Морские и промышленные двигатели Volvo Penta для судов и спецтехники.',
            ),
        ]
        extra_specs = [
            ('Epiroc', 80, 'Решения для бурения и горных работ Epiroc.'),
            ('Sandvik', 90, 'Оборудование и комплектующие Sandvik для тяжёлых условий эксплуатации.'),
        ]
        manufacturers: list[Manufacturer] = []
        for name, seed, desc in engine_specs + extra_specs:
            file_slug = _manufacturer_file_slug(name)
            m, _ = Manufacturer.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'ordering': seed,
                },
            )
            if not m.logo.name:
                m.logo.save(
                    f'logo_{file_slug}.jpg',
                    fake_image(f'logo_{file_slug}.jpg', 320, 200, seed),
                    save=True,
                )
            if not m.hero_image.name:
                m.hero_image.save(
                    f'hero_{file_slug}.jpg',
                    fake_image(f'hero_{file_slug}.jpg', 1200, 600, seed + 100),
                    save=True,
                )
            m.description = desc
            m.ordering = seed
            m.save()
            _ensure_manufacturer_seo(m)
            manufacturers.append(m)

        engine_brand_meta = {
            'Cummins': {
                'features_heading': '',
                'features': [],
            },
            'Caterpillar': {
                'features_heading': 'Особенности двигателей Caterpillar',
                'features': [
                    ('НАДЁЖНОСТЬ', 'Двигатели CAT рассчитаны на экстремальные нагрузки и длительную эксплуатацию.'),
                    ('ВЫНОСЛИВОСТЬ', 'Устойчивость к вибрации, пыли и перепадам температур в карьере и на стройке.'),
                    ('ТЕХНИЧЕСКОЕ ОБСЛУЖИВАНИЕ', 'Развитая сервисная сеть и доступность оригинальных комплектующих.'),
                ],
            },
            'Deutz': {
                'features_heading': 'Преимущества двигателей Deutz',
                'features': [
                    ('НАДЁЖНОСТЬ И ДОЛГОВЕЧНОСТЬ', 'Проверенные конструкции для непрерывной работы в тяжёлых условиях.'),
                    ('ИННОВАЦИОННЫЕ ТЕХНОЛОГИИ', 'Современные системы впрыска и управления двигателем.'),
                    ('ЭФФЕКТИВНОСТЬ И ЭКОНОМИЧНОСТЬ', 'Снижение эксплуатационных расходов при высокой производительности.'),
                ],
            },
            'Weichai': {'features_heading': '', 'features': []},
            'Komatsu': {'features_heading': '', 'features': []},
            'MTU': {'features_heading': '', 'features': []},
            'Perkins': {'features_heading': '', 'features': []},
            'Volvo Penta': {'features_heading': '', 'features': []},
        }
        manufacturer_by_name = {m.name: m for m in manufacturers}
        for brand_name, meta in engine_brand_meta.items():
            man = manufacturer_by_name.get(brand_name)
            if not man:
                continue
            man.features_heading = meta['features_heading']
            man.save(update_fields=['features_heading'])
            if meta['features']:
                man.features.all().delete()
                for order, (title, text) in enumerate(meta['features']):
                    ManufacturerFeature.objects.create(
                        manufacturer=man,
                        title=title,
                        description=text,
                        ordering=order,
                    )

        engine_samples = [
            ('Cummins', 'Двигатель Cummins ISF 2.8', 'ENG-CUM-ISF28', Decimal('485000.00')),
            ('Cummins', 'Двигатель Cummins QSB 6.7', 'ENG-CUM-QSB67', Decimal('920000.00')),
            ('Cummins', 'Двигатель Cummins QSL 9', 'ENG-CUM-QSL9', Decimal('1450000.00')),
            ('Caterpillar', 'Двигатель Caterpillar C7.1', 'ENG-CAT-C71', Decimal('1180000.00')),
            ('Caterpillar', 'Двигатель Caterpillar C9.3', 'ENG-CAT-C93', Decimal('1680000.00')),
            ('Caterpillar', 'Двигатель Caterpillar C13', 'ENG-CAT-C13', Decimal('2100000.00')),
            ('Deutz', 'Двигатель Deutz TCD 2.2 L3', 'ENG-DEU-TCD22', Decimal('560000.00')),
            ('Deutz', 'Двигатель Deutz TCD 6.1 L6', 'ENG-DEU-TCD61', Decimal('980000.00')),
            ('Deutz', 'Двигатель Deutz TCD 7.8 L6', 'ENG-DEU-TCD78', Decimal('1320000.00')),
            ('Weichai', 'Двигатель Weichai WP10', 'ENG-WEI-WP10', Decimal('740000.00')),
            ('Weichai', 'Двигатель Weichai WP12', 'ENG-WEI-WP12', Decimal('890000.00')),
            ('Komatsu', 'Двигатель Komatsu SAA6D107E', 'ENG-KOM-SAA6D107', Decimal('1350000.00')),
            ('Komatsu', 'Двигатель Komatsu SAA6D125E', 'ENG-KOM-SAA6D125', Decimal('1580000.00')),
            ('MTU', 'Двигатель MTU Series 1000', 'ENG-MTU-1000', Decimal('2450000.00')),
            ('MTU', 'Двигатель MTU Series 1500', 'ENG-MTU-1500', Decimal('3100000.00')),
            ('Perkins', 'Двигатель Perkins 1104C-44TA', 'ENG-PER-1104C44', Decimal('620000.00')),
            ('Perkins', 'Двигатель Perkins 1206F-E70TTA', 'ENG-PER-1206F70', Decimal('780000.00')),
            ('Volvo Penta', 'Двигатель Volvo Penta TAD650VE', 'ENG-VOL-TAD650', Decimal('1120000.00')),
            ('Volvo Penta', 'Двигатель Volvo Penta TAD881VE', 'ENG-VOL-TAD881', Decimal('1490000.00')),
        ]

        spare_samples = [
            ('9Y7573 ПЛАТА КРЕПЛЕНИЯ КОМПРЕССОРА CAT', '2047330', 'Caterpillar', Decimal('28600.00')),
            ('ФИЛЬТР МАСЛЯНЫЙ CAT', '1R-0716', 'Caterpillar', Decimal('4250.50')),
            ('ТУРБОКОМПРЕССОР CUMMINS HE351', '4038597', 'Cummins', Decimal('125900.00')),
            ('ВОДЯНОЙ НАСОС DEUTZ 1013', '04259547', 'Deutz', Decimal('18900.00')),
            ('ПЛАНЕТАРНЫЙ РЕДУКТОР KOMATSU', '55555-00011', 'Komatsu', Decimal('340000.00')),
            ('БУРОВОЙ НАКОНЕЧНИК EPIROC', 'EPI-7721', 'Epiroc', Decimal('78500.00')),
            ('ФИЛЬТР ВОЗДУШНЫЙ SANDVIK', 'SNV-AF90', 'Sandvik', Decimal('6200.00')),
        ]
        tire_samples = [
            ('Шина 23.5-25 E-3/L-3 TL', 'TIRE-23525', Decimal('185000.00')),
            ('Шина 26.5R25 ** для карьерного самосвала', 'TIRE-26525', Decimal('210000.00')),
            ('Шина 29.5R29 для погрузчика', 'TIRE-29529', Decimal('295000.00')),
        ]

        pid = 0
        for i, (title, art, brand_name, price) in enumerate(spare_samples):
            pid += 1
            man = manufacturer_by_name[brand_name]
            p, _ = Product.objects.update_or_create(
                artikul=art,
                defaults={
                    'product_type': ProductType.SPARE_PARTS,
                    'manufacturer': man,
                    'name': title,
                    'description': (
                        f'Оригинал / сертифицированный аналог. Артикул {art}. '
                        'Уточняйте применимость по VIN и серийному номеру техники.'
                    ),
                    'price': price,
                    'is_stock': i % 4 != 2,
                    'ordering': i,
                },
            )
            _ensure_product_seo(p)
            if not p.images.exists():
                for o in range(2):
                    img = ProductImage(product=p, ordering=o)
                    img.image.save(f'prod_{p.pk}_{o}.jpg', fake_image(f'p{p.pk}_{o}.jpg', 500, 500, pid + o), save=True)
            else:
                _ensure_product_images(p, pid)

        for i, (brand_name, title, art, price) in enumerate(engine_samples):
            pid += 1
            man = manufacturer_by_name[brand_name]
            p, _ = Product.objects.update_or_create(
                artikul=art,
                defaults={
                    'product_type': ProductType.ENGINES,
                    'manufacturer': man,
                    'name': title,
                    'description': '',
                    'price': price,
                    'is_stock': True,
                    'ordering': 200 + i,
                },
            )
            _ensure_product_seo(p)
            if not p.images.exists():
                for o in range(1):
                    img = ProductImage(product=p, ordering=o)
                    img.image.save(
                        f'engine_{p.pk}_{o}.jpg',
                        fake_image(f'eng{p.pk}_{o}.jpg', 500, 500, pid + o),
                        save=True,
                    )
            else:
                _ensure_product_images(p, pid)

        for i, (title, art, price) in enumerate(tire_samples):
            pid += 1
            man = manufacturer_by_name['Caterpillar']
            p, _ = Product.objects.update_or_create(
                artikul=art,
                defaults={
                    'product_type': ProductType.TIRES,
                    'manufacturer': man,
                    'name': title,
                    'description': 'Шина для карьерной и дорожно-строительной техники. Поставка под заказ и со склада.',
                    'price': price,
                    'is_stock': True,
                    'ordering': 100 + i,
                },
            )
            _ensure_product_seo(p)
            if not p.images.exists():
                for o in range(2):
                    img = ProductImage(product=p, ordering=o)
                    img.image.save(f'prod_{p.pk}_{o}.jpg', fake_image(f'pt{p.pk}_{o}.jpg', 500, 500, pid + o), save=True)
            else:
                _ensure_product_images(p, pid)

    def _seed_banners(self) -> None:
        if Banner.objects.exists():
            return
        slides = [
            (
                'ШИНЫ ДЛЯ РАБОТЫ БЕЗ ПРОСТОЕВ',
                'НАДЕЖНОСТЬ',
                'Поставляем шины для спецтехники с оптимальным ресурсом, сцеплением и устойчивостью к износу',
            ),
            (
                'ЗАПЧАСТИ В НАЛИЧИИ И ПОД ЗАКАЗ',
                'КАЧЕСТВО',
                'Быстрая логистика по России. Проверенные поставщики и гарантия подлинности.',
            ),
            (
                'ПАРТНЁРЫ МИРОВЫХ БРЕНДОВ',
                'ПАРТНЁРСТВО',
                'Caterpillar, Cummins, Deutz, Komatsu и другие производители — одно окно для вашей техники.',
            ),
        ]
        for i, (title, slide_type, desc) in enumerate(slides):
            b = Banner(title=title, type=slide_type, description=desc, ordering=i, is_active=True)
            b.image.save(f'banner_{i}.jpg', fake_image(f'banner_{i}.jpg', 1600, 640, 300 + i), save=True)

    def _seed_certifications(self) -> None:
        if Certification.objects.exists():
            return
        today = timezone.localdate()
        samples = [
            ('Сертификат доверия', 780),
            ('Сертификат соответствия', 512),
            ('Сертификат официального дилера', 640),
            ('Сертификат качества поставок', 420),
            ('Сертификат партнёрства Cummins', 890),
        ]
        for i, (base_name, pdf_kb) in enumerate(samples):
            issued = today - timedelta(days=14 + i * 45)
            name = f'{base_name} от {issued.strftime("%d.%m.%Y")}'
            cert = Certification(name=name)
            cert.thumbnail_image.save(
                f'cert_thumb_{i}.jpg',
                fake_image(f'cert_{i}.jpg', 400, 560, 700 + i),
                save=False,
            )
            cert.pdf.save(f'cert_{i}.pdf', fake_pdf(f'cert_{i}.pdf', pdf_kb), save=True)

    def _seed_news(self) -> None:
        if News.objects.exists():
            return
        today = timezone.localdate()

        items = [
            (
                'ЗАПЧАСТИ ДЛЯ СПЕЦТЕХНИКИ САНКТ-ПЕТЕРБУРГ',
                NewsType.USEFUL,
                'Обзор складских позиций и сроков поставки по Северо-Западу.',
            ),
            (
                'НОВИНКИ КАТАЛОГА: ФИЛЬТРЫ И ГИДРАВЛИКА',
                NewsType.USEFUL,
                'Расширение линейки расходников для карьерной и строительной техники.',
            ),
            (
                'МАКСАН ГРУПП НА ОТРАСЛЕВОМ МЕРОПРИЯТИИ',
                NewsType.COMPANY,
                'Встреча с партнёрами и презентация новых контрактов по поставкам.',
            ),
            (
                'КАК ВЫБРАТЬ ШИНЫ ДЛЯ САМОСВАЛОВ',
                NewsType.USEFUL,
                'Краткое руководство: индексы нагрузки, глубина протектора, условия эксплуатации.',
            ),
            (
                'ОБНОВЛЕНИЕ САЙТА И ЛИЧНЫХ КАБИНЕТОВ НЕ ПРЕДУСМОТРЕНО — ГОСТЕВОЙ ЗАКАЗ',
                NewsType.COMPANY,
                'Заказ и консультации через формы и телефон — без обязательной регистрации.',
            ),
        ]
        for i, (title, ntype, short) in enumerate(items):
            pub = today - timedelta(days=i * 7 + random.randint(0, 3))
            n = News.objects.create(
                title=title,
                news_type=ntype,
                description=short + '\n\n' + 'Дополнительные детали у менеджеров отдела продаж.',
                published_at=pub,
                ordering=i,
            )
            for o in range(2):
                ni = NewsImage(news=n, ordering=o)
                ni.image.save(f'news_{n.pk}_{o}.jpg', fake_image(f'n{n.pk}_{o}.jpg', 900, 600, 500 + n.pk + o), save=True)

    def _seed_feedback(self) -> None:
        demo_emails = ('demo.lead1@example.com', 'demo.lead2@example.com', 'client.spb@example.com')
        payloads = [
            ('Александр', demo_emails[0], '+7 (921) 900-11-22'),
            ('Мария Петрова', demo_emails[1], '+7 (921) 200-33-44'),
            ('ООО «Карьер-Сервис»', demo_emails[2], '+7 (812) 555-66-77'),
        ]
        for name, email, phone in payloads:
            FeedbackMessage.objects.get_or_create(
                email=email,
                defaults={'full_name': name, 'phone': phone},
            )

    def _seed_orders(self) -> None:
        if Order.objects.exists():
            return
        products = list(Product.objects.order_by('pk')[:2])
        if len(products) < 2:
            return
        a, b = products[0], products[1]
        q1, q2 = 1, 2
        t1 = a.price * q1
        t2 = b.price * q2
        total = t1 + t2
        order = Order.objects.create(
            full_name='Иван Тестов',
            phone='+7 (921) 777-88-99',
            total_price=total,
            is_seen_moderator=False,
        )
        OrderProduct.objects.create(order=order, product=a, quantity=q1, total_price=t1)
        OrderProduct.objects.create(order=order, product=b, quantity=q2, total_price=t2)
