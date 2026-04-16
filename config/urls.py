from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("assistant/", include("apps.assistant.urls")),
    path("", include("apps.core.urls")),
    path("repository/", include("apps.repository.urls")),
    path("search/", include("apps.search.urls")),
]
