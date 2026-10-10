"""Письма о новых заказах: запчасти и двигатели — на info, шины — на почту по шинам."""
from __future__ import annotations

import logging
from collections import OrderedDict
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from commerce.models import Order, OrderProduct, ProductType

logger = logging.getLogger(__name__)

PRICE_ON_REQUEST_LABEL = 'Цена по запросу'


def _recipients() -> tuple[str, str]:
    from leads.models import Contact

    contact = Contact.objects.filter(pk=1).first()
    spare_parts = (contact.email_spare_parts if contact else '') or settings.ORDER_EMAIL_SPARE_PARTS
    tires = (contact.email_tires if contact else '') or settings.ORDER_EMAIL_TIRES
    return spare_parts.strip(), tires.strip()


def _group_items_by_recipient(items: list[OrderProduct]) -> OrderedDict[str, list[OrderProduct]]:
    spare_parts_email, tires_email = _recipients()
    groups: OrderedDict[str, list[OrderProduct]] = OrderedDict()
    for item in items:
        is_tire = item.product.product_type == ProductType.TIRES
        recipient = tires_email if is_tire else spare_parts_email
        if recipient:
            groups.setdefault(recipient, []).append(item)
    return groups


def _format_money(value: Decimal) -> str:
    return f'{value:,.2f}'.replace(',', ' ').replace('.', ',') + ' ₽'


def _build_message(order: Order, items: list[OrderProduct]) -> tuple[str, str]:
    types = {item.product.get_product_type_display() for item in items}
    subject = f'Заявка №{order.pk} с сайта — {", ".join(sorted(types))}'

    created = timezone.localtime(order.created_at).strftime('%d.%m.%Y %H:%M')
    lines = [
        f'Новая заявка №{order.pk} с сайта ООО «МАКСАН ГРУПП»',
        '',
        f'Имя: {order.full_name}',
        f'Телефон: {order.phone}',
        f'Дата: {created}',
        '',
        'Товары:',
    ]
    priced_total = Decimal('0')
    has_on_request = False
    for index, item in enumerate(items, start=1):
        product = item.product
        details = [product.name]
        if product.artikul:
            details.append(f'арт. {product.artikul}')
        details.append(product.manufacturer.name)
        details.append(f'{item.quantity} шт.')
        if item.price_on_request:
            has_on_request = True
            details.append(PRICE_ON_REQUEST_LABEL)
        else:
            priced_total += item.total_price
            details.append(_format_money(item.total_price))
        lines.append(f'{index}. ' + ' — '.join(details))

    lines.append('')
    lines.append(f'Сумма по позициям с ценой: {_format_money(priced_total)}')
    if has_on_request:
        lines.append(f'Есть позиции «{PRICE_ON_REQUEST_LABEL}» — уточните стоимость у клиента.')
    lines.append('')
    lines.append(f'Открыть в админке: {settings.PUBLIC_SITE_URL}/admin/commerce/order/{order.pk}/change/')
    return subject, '\n'.join(lines)


def send_order_notifications(order_id: int) -> int:
    """Отправляет письма по заказу. Возвращает число отправленных писем; ошибки только логирует."""
    order = Order.objects.get(pk=order_id)
    items = list(
        order.items.select_related('product__manufacturer').order_by('id'),
    )
    if settings.EMAIL_BACKEND.endswith('console.EmailBackend'):
        logger.warning(
            'Заказ #%s: SMTP не настроен (EMAIL_HOST_USER / EMAIL_HOST_PASSWORD пусты) — письмо не уйдёт на почту.',
            order_id,
        )

    sent = 0
    for recipient, recipient_items in _group_items_by_recipient(items).items():
        subject, body = _build_message(order, recipient_items)
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
            sent += 1
        except Exception:
            logger.exception('Не удалось отправить письмо о заказе #%s на %s', order_id, recipient)
    return sent
