from django.urls import path

from .views import health_view, home_view, legacy_home_view, live_home_view

urlpatterns = [
    path("", home_view, name="home"),
    path("live/", live_home_view, name="live-home"),
    path("legacy/", legacy_home_view, name="legacy-home"),
    path("health/", health_view, name="health"),
]
