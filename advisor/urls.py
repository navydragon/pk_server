from django.urls import path

from .views import AdvisorChatView, AdvisorFiltersView

urlpatterns = [
    path('filters/', AdvisorFiltersView.as_view(), name='advisor-filters'),
    path('chat/', AdvisorChatView.as_view(), name='advisor-chat'),
]
