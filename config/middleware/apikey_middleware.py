"""Необязательный API-ключ для внутренних интеграций (выключен по умолчанию)."""
from django.conf import settings
from django.http import JsonResponse


class BackendApiKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, 'REQUIRE_BACKEND_API_KEY', False):
            return self.get_response(request)
        key = getattr(settings, 'BACKEND_API_KEY', '') or ''
        if not key:
            return self.get_response(request)
        supplied = request.headers.get('X-Backend-Api-Key', '')
        if supplied != key:
            return JsonResponse({'detail': 'Invalid API key'}, status=401)
        return self.get_response(request)
