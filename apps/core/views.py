from __future__ import annotations

from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render

from apps.repository.models import RepositoryRecord


def home_view(request):
    dataset_counts = {
        item["source_dataset"]: item["count"]
        for item in RepositoryRecord.objects.values("source_dataset").annotate(count=Count("id"))
    }
    context = {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "initial_input_dir": settings.INITIAL_INPUT_DIR.name,
        "total_records": RepositoryRecord.objects.count(),
        "dataset_counts": dataset_counts,
    }
    return render(request, "core/home.html", context)


def health_view(request):
    return JsonResponse(
        {
            "status": "ok",
            "app": settings.APP_NAME,
            "environment": settings.APP_ENV,
        }
    )
