import logging

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from leads.models import Contact
from leads.notifications import send_feedback_notification
from leads.serializers import FeedbackMessageSerializer, SiteContactSerializer

logger = logging.getLogger(__name__)


def _notify_about_feedback(message_id: int) -> None:
    try:
        send_feedback_notification(message_id)
    except Exception:
        logger.exception('Ошибка при отправке уведомления о заявке #%s', message_id)


def _persist_feedback(data):
    serializer = FeedbackMessageSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    msg = serializer.save()
    transaction.on_commit(lambda: _notify_about_feedback(msg.pk))
    return msg


class FeedbackCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Обращения'],
        summary='Отправить форму «Остались вопросы?»',
        description=(
            'Обратная связь с сайта без регистрации. '
            'Письмо уходит на info@ (email запчастей / общие заявки).'
        ),
        responses={201: None},
        request=FeedbackMessageSerializer,
    )
    def post(self, request):
        _persist_feedback(dict(request.data))
        return Response({'detail': 'Сообщение принято.'}, status=status.HTTP_201_CREATED)


class SiteContactView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Контакты'],
        summary='Страница контактов',
        description='Адрес, email по направлениям и блок телефонов с ссылками.',
        responses={200: SiteContactSerializer},
    )
    def get(self, request):
        Contact.objects.get_or_create(
            pk=1,
            defaults={
                'address': '',
                'email_spare_parts': '',
                'email_tires': '',
            },
        )
        obj = Contact.objects.prefetch_related('phones').get(pk=1)
        serializer = SiteContactSerializer(obj)
        return Response(serializer.data)
