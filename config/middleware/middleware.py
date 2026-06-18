from django.http import Http404, JsonResponse
from rest_framework import status
import logging
import traceback


class JsonErrorResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)

    def __call__(self, request):
        # Get the response from the view function
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            return None

        # Skip middleware for schema/docs endpoints
        if request.path in ['/schema/', '/docs/', '/redoc/']:
            return None  # Let Django handle it normally

        # Skip middleware for admin and media static files
        if request.path.startswith('/admin/') or request.path.startswith('/media/'):
            return None

        # Log full traceback to console/logs for debugging
        self.logger.exception("Unhandled exception for path %s", request.path, exc_info=exception)
        traceback.print_exc()

        # Process exceptions and return JSON error response
        response_data = {"detail": "Внутренняя ошибка сервера"}
        return JsonResponse(response_data, status=500)


# Middleware for handling custom 404 responses
class Custom404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the response from the view function
        response = self.get_response(request)
        
        # Only handle 404 for non-API requests
        if request.path.startswith('/api/'):
            return response

        if request.path.startswith('/admin/') or request.path.startswith('/media/'):
            return response

        if response is None:
            # If response is None, handle 404 error
            return self.handle_404(request)

        if response.status_code == status.HTTP_404_NOT_FOUND:
            # If response status is 404, handle 404 error
            return self.handle_404(request)

        return response

    def handle_404(self, request):
        # Handle 404 error and return JSON response
        data = {"detail": "Страница не найдена"}
        return JsonResponse(data, status=status.HTTP_404_NOT_FOUND)