from __future__ import annotations

from pathlib import Path

from django.db.models import Count, Q

from .models import Country, Hazard, ImportBatch, NbsType, RepositoryRecord
from .source_specs import get_source_specs
from .validation import RepositorySourceValidator


def build_repository_qa_report(input_dir: Path, batch_id: int | None = None) -> dict:
    specs = get_source_specs()
    validation_results = RepositorySourceValidator(input_dir=input_dir).validate_specs(specs)

    queryset = RepositoryRecord.objects.all()
    selected_batch = None
    if batch_id is not None:
        selected_batch = ImportBatch.objects.filter(pk=batch_id).first()
        queryset = queryset.filter(import_batch_id=batch_id)

    total_records = queryset.count()
    dataset_counts = {
        item["source_dataset"]: item["doc_count"]
        for item in queryset.values("source_dataset").annotate(doc_count=Count("id"))
    }
    validated_counts = {result.dataset: result.row_count for result in validation_results}

    comparison = []
    for spec in specs:
        validated = validated_counts.get(spec.dataset, 0)
        imported = dataset_counts.get(spec.dataset, 0)
        comparison.append(
            {
                "dataset": spec.dataset,
                "validated_row_count": validated,
                "imported_record_count": imported,
                "difference": imported - validated,
            }
        )

    taxonomy_counts = {
        "countries": Country.objects.count(),
        "hazards": Hazard.objects.count(),
        "nbs_types": NbsType.objects.count(),
    }

    geocoded_total = queryset.filter(latitude__isnull=False, longitude__isnull=False).count()
    geocoding_by_dataset = list(
        queryset.values("source_dataset")
        .annotate(
            total=Count("id"),
            geocoded=Count("id", filter=Q(latitude__isnull=False, longitude__isnull=False)),
            approximate=Count(
                "id",
                filter=Q(normalized_payload__geo_precision="country_centroid"),
            ),
        )
        .order_by("source_dataset")
    )
    for item in geocoding_by_dataset:
        total = item["total"] or 0
        item["coverage_pct"] = round((item["geocoded"] / total) * 100, 1) if total else 0.0

    field_gaps = {
        "missing_year": queryset.filter(
            publication_year__isnull=True,
            start_year__isnull=True,
            end_year__isnull=True,
        ).count(),
        "missing_country_display": queryset.filter(country_display="").count(),
        "missing_source_url": queryset.filter(source_url="", source_url_secondary="").count(),
        "missing_geolocation": queryset.filter(
            Q(latitude__isnull=True) | Q(longitude__isnull=True)
        ).count(),
        "missing_searchable_summary": queryset.filter(
            abstract="",
            summary="",
            description="",
            objective="",
            lessons="",
        ).count(),
        "derived_country_display": queryset.filter(
            normalized_payload__country_display_source__in=["country_code", "geographic_focus", "geographic_scope"]
        ).count(),
        "approximate_country_centroid_geocoding": queryset.filter(
            normalized_payload__geo_precision="country_centroid"
        ).count(),
        "missing_hazard_taxonomy": queryset.filter(
            primary_hazards__isnull=True,
            secondary_hazards__isnull=True,
        ).distinct().count(),
        "missing_nbs_type_taxonomy": queryset.filter(
            primary_nbs_types__isnull=True,
            secondary_nbs_types__isnull=True,
        ).distinct().count(),
        "missing_country_taxonomy": queryset.filter(countries__isnull=True).distinct().count(),
    }

    batch_summary = None
    if selected_batch is not None:
        batch_summary = {
            "id": selected_batch.id,
            "source_label": selected_batch.source_label,
            "records_imported": selected_batch.records_imported,
            "started_at": selected_batch.started_at,
            "completed_at": selected_batch.completed_at,
        }

    return {
        "scope": "batch" if selected_batch is not None else "repository",
        "batch": batch_summary,
        "total_records": total_records,
        "validated_sources": [
            {
                "dataset": result.dataset,
                "filename": result.filename,
                "sheet_name": result.sheet_name,
                "status": result.status,
                "row_count": result.row_count,
                "column_count": result.column_count,
                "duplicate_source_ids": result.duplicate_source_ids,
                "missing_required_columns": result.missing_required_columns,
                "messages": result.messages,
            }
            for result in validation_results
        ],
        "import_vs_validation": comparison,
        "taxonomy_counts": taxonomy_counts,
        "geocoding": {
            "geocoded_records": geocoded_total,
            "missing_geocoding_records": total_records - geocoded_total,
            "by_dataset": geocoding_by_dataset,
        },
        "field_gaps": field_gaps,
    }
