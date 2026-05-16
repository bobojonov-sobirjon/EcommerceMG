from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from leads.models import Contact
from leads.serializers import FeedbackMessageSerializer, SiteContactSerializer


def _persist_feedback(data):
    serializer = FeedbackMessageSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()


class FeedbackCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Обращения'],
        summary='Отправить форму «Остались вопросы?»',
        description='Обратная связь с сайта без регистрации.',
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
