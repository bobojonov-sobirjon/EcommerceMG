"""Проверка SMTP: отправляет тестовое письмо и показывает, куда уходят заказы."""
from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from commerce.notifications import _recipients


class Command(BaseCommand):
    help = 'Отправляет тестовое письмо и показывает настройки почты для заказов.'

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, default='', help='Куда отправить (по умолчанию — почта запчастей)')

    def handle(self, *args, **options):
        spare_parts, tires = _recipients()
        self.stdout.write(f'EMAIL_BACKEND:      {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST:PORT:    {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        self.stdout.write(f'TLS / SSL:          {settings.EMAIL_USE_TLS} / {settings.EMAIL_USE_SSL}')
        self.stdout.write(f'EMAIL_HOST_USER:    {settings.EMAIL_HOST_USER or "(пусто)"}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Заказы запчасти/двигатели -> {spare_parts or "(не задано)"}')
        self.stdout.write(f'Заказы шины               -> {tires or "(не задано)"}')

        if settings.EMAIL_BACKEND.endswith('console.EmailBackend'):
            self.stdout.write(self.style.ERROR(
                'SMTP не настроен: в .env нужны EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD.',
            ))
            return

        to = (options['to'] or spare_parts).strip()
        send_mail(
            'Тест почты — сайт МАКСАН ГРУПП',
            'Если вы видите это письмо, уведомления о заказах будут приходить на почту.',
            settings.DEFAULT_FROM_EMAIL,
            [to],
            fail_silently=False,
        )
        self.stdout.write(self.style.SUCCESS(f'Тестовое письмо отправлено на {to}'))
