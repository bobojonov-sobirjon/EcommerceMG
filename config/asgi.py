"""
ASGI-приложение для **Daphne** (и других ASGI-серверов).

Запуск вручную:
    daphne -b 0.0.0.0 -p 8000 config.asgi:application

Переменные окружения (опционально):
    DAPHNE_BIND   — хост (по умолчанию в скрипте)
    DAPHNE_PORT   — порт

При `daphne` в начале INSTALLED_APPS команда `manage.py runserver` также
использует ASGI-сервер Daphne для разработки.
"""
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_http_application = get_asgi_application()

from config.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        'http': django_http_application,
        'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
