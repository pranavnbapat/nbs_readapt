from django.urls import path

from .views import assistant_chat_view, assistant_status_view

urlpatterns = [
    path("status/", assistant_status_view, name="assistant-status"),
    path("chat/", assistant_chat_view, name="assistant-chat"),
]
