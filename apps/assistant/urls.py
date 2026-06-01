from django.urls import path

from .views import (
    assistant_chat_stream_view,
    assistant_chat_view,
    assistant_login_view,
    assistant_logout_view,
    assistant_session_view,
    assistant_status_view,
)

urlpatterns = [
    path("login/", assistant_login_view, name="assistant-login"),
    path("logout/", assistant_logout_view, name="assistant-logout"),
    path("session/", assistant_session_view, name="assistant-session"),
    path("status/", assistant_status_view, name="assistant-status"),
    path("chat/", assistant_chat_view, name="assistant-chat"),
    path("chat/stream/", assistant_chat_stream_view, name="assistant-chat-stream"),
]
