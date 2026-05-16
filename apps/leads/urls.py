from django.urls import path

from leads.views import FeedbackCreateView, SiteContactView

urlpatterns = [
    path('messages/', FeedbackCreateView.as_view()),
    path('contacts/', SiteContactView.as_view()),
]
