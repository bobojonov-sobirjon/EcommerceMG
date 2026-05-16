from django.urls import path

from commerce.views import (
    ManufacturerDetailView,
    ManufacturerListView,
    OrderCreateView,
    ProductDetailView,
    ProductListView,
    ProductSimilarView,
)

urlpatterns = [
    path('manufacturers/', ManufacturerListView.as_view()),
    path('manufacturers/<int:pk>/', ManufacturerDetailView.as_view()),
    path('products/', ProductListView.as_view()),
    path('products/<int:pk>/similar/', ProductSimilarView.as_view()),
    path('products/<int:pk>/', ProductDetailView.as_view()),
    path('orders/', OrderCreateView.as_view()),
]
