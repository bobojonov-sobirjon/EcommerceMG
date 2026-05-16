"""Проходная обёртка для ASGI JSON-ошибок (заготовка проекта)."""
from django.http import JsonResponse


class JsonErrorResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)


class Custom404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404 and request.path.startswith('/api/'):
            return JsonResponse({'detail': 'Not found'}, status=404)
        return response
