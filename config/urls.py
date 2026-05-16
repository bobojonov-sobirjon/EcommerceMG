from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import never_cache

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('config.api_v1_urls')),
]

urlpatterns += [
    path('schema/', never_cache(SpectacularAPIView.as_view()), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

urlpatterns += [
    
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT, }, ), ]


def _unregister_unused_admin_models() -> None:
    """Скрыть стандартные разделы админки, которые не используются в проекте."""
    for model in (Group, User, Site):
        try:
            admin.site.unregister(model)
        except admin.sites.NotRegistered:
            pass


_unregister_unused_admin_models()