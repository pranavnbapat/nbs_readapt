from __future__ import annotations

from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect, render

from apps.repository.models import RepositoryRecord


def _home_context():
    dataset_counts = {
        item["source_dataset"]: item["count"]
        for item in RepositoryRecord.objects.values("source_dataset").annotate(count=Count("id"))
    }
    total_records = RepositoryRecord.objects.count()
    geocoded_records = RepositoryRecord.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True).count()
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "initial_input_dir": settings.INITIAL_INPUT_DIR.name,
        "total_records": total_records,
        "dataset_counts": dataset_counts,
        "geocoded_records": geocoded_records,
        "country_count": RepositoryRecord.objects.filter(countries__isnull=False).values("countries").distinct().count(),
    }


def home_view(request):
    return render(request, "core/home_reference.html", _home_context())


def live_home_view(request):
    return redirect("home")


def legacy_home_view(request):
    return render(request, "core/home_legacy.html", _home_context())


def health_view(request):
    return JsonResponse(
        {
            "status": "ok",
            "app": settings.APP_NAME,
            "environment": settings.APP_ENV,
        }
    )
