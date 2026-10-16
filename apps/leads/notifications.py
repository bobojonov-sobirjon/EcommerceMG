"""Письма по форме обратной связи — на info@ (все заявки, кроме заказов шин)."""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from leads.models import FeedbackMessage

logger = logging.getLogger(__name__)


def _feedback_recipient() -> str:
    from leads.models import Contact

    contact = Contact.objects.filter(pk=1).first()
    email = (contact.email_spare_parts if contact else '') or settings.ORDER_EMAIL_SPARE_PARTS
    return email.strip()


def send_feedback_notification(message_id: int) -> bool:
    """Отправляет письмо о заявке с формы. Ошибки только логирует."""
    msg = FeedbackMessage.objects.get(pk=message_id)
    recipient = _feedback_recipient()
    if not recipient:
        logger.warning('Заявка #%s: получатель email не задан — письмо не отправлено.', message_id)
        return False

    if settings.EMAIL_BACKEND.endswith('console.EmailBackend'):
        logger.warning(
            'Заявка #%s: SMTP не настроен (EMAIL_HOST_USER / EMAIL_HOST_PASSWORD пусты).',
            message_id,
        )

    created = timezone.localtime(msg.created_at).strftime('%d.%m.%Y %H:%M')
    subject = f'Заявка с сайта — {msg.full_name}'
    body = '\n'.join(
        [
            'Новая заявка с формы «Остались вопросы?»',
            '',
            f'Имя: {msg.full_name}',
            f'Email: {msg.email}',
            f'Телефон: {msg.phone}',
            f'Дата: {created}',
            '',
            f'Открыть в админке: {settings.PUBLIC_SITE_URL}/admin/leads/feedbackmessage/{msg.pk}/change/',
        ]
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        return True
    except Exception:
        logger.exception('Не удалось отправить письмо о заявке #%s на %s', message_id, recipient)
        return False
