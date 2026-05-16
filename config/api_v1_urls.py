"""Конечные точки версии API v1."""
from django.urls import include, path

urlpatterns = [
    path('', include('content.urls')),
    path('', include('commerce.urls')),
    path('', include('leads.urls')),
]
