from django.urls import path

from content.views import AboutCompanyView, BannerListView, NewsDetailView, NewsListView

urlpatterns = [
    path('banners/', BannerListView.as_view()),
    path('about/', AboutCompanyView.as_view()),
    path('news/', NewsListView.as_view()),
    path('news/<int:pk>/', NewsDetailView.as_view()),
]
