from django.urls import path

from .views import repository_overview_view, repository_qa_view, repository_status_view
from .views_record import record_detail_view

urlpatterns = [
    path("", repository_status_view, name="repository-status"),
    path("overview/", repository_overview_view, name="repository-overview"),
    path("qa/", repository_qa_view, name="repository-qa"),
    path("records/<int:pk>/", record_detail_view, name="repository-record-detail"),
]
