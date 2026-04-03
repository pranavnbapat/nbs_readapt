from django.conf import settings
from django.db.models import Count
from django.db.models.functions import Coalesce
from django.http import JsonResponse

from .models import RepositoryRecord
from .qa import build_repository_qa_report


def repository_status_view(request):
    return JsonResponse(
        {
            "module": "repository",
            "status": "scaffolded",
            "initial_input_exists": settings.INITIAL_INPUT_DIR.exists(),
        }
    )


def repository_overview_view(request):
    total_records = RepositoryRecord.objects.count()

    dataset_counts = list(
        RepositoryRecord.objects.values("source_dataset")
        .annotate(doc_count=Count("id"))
        .order_by("-doc_count")
    )
    implementation_stage = list(
        RepositoryRecord.objects.exclude(implementation_stage="")
        .values("implementation_stage")
        .annotate(doc_count=Count("id"))
        .order_by("-doc_count")
    )
    year_counts = list(
        RepositoryRecord.objects.annotate(source_year=Coalesce("publication_year", "start_year", "end_year"))
        .exclude(source_year__isnull=True)
        .values("source_year")
        .annotate(doc_count=Count("id"))
        .order_by("source_year")
    )

    return JsonResponse(
        {
            "total_records": total_records,
            "dataset_counts": dataset_counts,
            "implementation_stage": implementation_stage,
            "year_counts": year_counts,
        }
    )


def repository_qa_view(request):
    batch_id = request.GET.get("batch_id")
    report = build_repository_qa_report(
        input_dir=settings.INITIAL_INPUT_DIR,
        batch_id=int(batch_id) if batch_id else None,
    )
    return JsonResponse(report)
