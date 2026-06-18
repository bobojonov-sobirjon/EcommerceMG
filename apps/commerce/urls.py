from django.urls import path

from commerce.views import (
    CatalogCategoriesView,
    EngineManufacturerListView,
    EngineManufacturerPageByIdView,
    EngineManufacturerPageBySlugView,
    ManufacturerDetailBySlugView,
    ManufacturerDetailView,
    ManufacturerListView,
    OrderCreateView,
    ProductDetailBySlugView,
    ProductDetailView,
    ProductListView,
    ProductSimilarBySlugView,
    ProductSimilarView,
)

urlpatterns = [
    path('catalog/categories/', CatalogCategoriesView.as_view()),
    path('engines/manufacturers/', EngineManufacturerListView.as_view()),
    path('engines/manufacturers/slug/<slug:slug>/', EngineManufacturerPageBySlugView.as_view()),
    path('engines/manufacturers/<int:pk>/', EngineManufacturerPageByIdView.as_view()),
    path('manufacturers/', ManufacturerListView.as_view()),
    path('manufacturers/slug/<slug:slug>/', ManufacturerDetailBySlugView.as_view()),
    path('manufacturers/<int:pk>/', ManufacturerDetailView.as_view()),
    path('products/', ProductListView.as_view()),
    path('products/slug/<slug:slug>/similar/', ProductSimilarBySlugView.as_view()),
    path('products/slug/<slug:slug>/', ProductDetailBySlugView.as_view()),
    path('products/<int:pk>/similar/', ProductSimilarView.as_view()),
    path('products/<int:pk>/', ProductDetailView.as_view()),
    path('orders/', OrderCreateView.as_view()),
]
