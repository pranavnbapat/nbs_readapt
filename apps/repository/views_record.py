from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import RepositoryRecord


def record_detail_view(request, pk: int):
    record = get_object_or_404(
        RepositoryRecord.objects.prefetch_related(
            "countries",
            "primary_hazards",
            "secondary_hazards",
            "primary_nbs_types",
            "secondary_nbs_types",
        ),
        pk=pk,
    )
    return JsonResponse(
        {
            "id": record.id,
            "title": record.title,
            "source_dataset": record.source_dataset,
            "source_uid": record.source_uid,
            "source_record_id": record.source_record_id,
            "source_sheet": record.source_sheet,
            "publication_year": record.publication_year,
            "start_year": record.start_year,
            "end_year": record.end_year,
            "country_display": record.country_display,
            "city_location": record.city_location,
            "source_url": record.source_url,
            "source_url_secondary": record.source_url_secondary,
            "summary": record.summary,
            "abstract": record.abstract,
            "description": record.description,
            "objective": record.objective,
            "outcomes_targeted": record.outcomes_targeted,
            "ecological_impacts": record.ecological_impacts,
            "socio_economic_impacts": record.socio_economic_impacts,
            "governance_insights": record.governance_insights,
            "finance_insights": record.finance_insights,
            "implementation_steps": record.implementation_steps,
            "barriers": record.barriers,
            "enablers": record.enablers,
            "lessons": record.lessons,
            "keywords": record.keywords,
            "countries": list(record.countries.values_list("name", flat=True)),
            "primary_hazards": list(record.primary_hazards.values_list("name", flat=True)),
            "secondary_hazards": list(record.secondary_hazards.values_list("name", flat=True)),
            "primary_nbs_types": list(record.primary_nbs_types.values_list("name", flat=True)),
            "secondary_nbs_types": list(record.secondary_nbs_types.values_list("name", flat=True)),
        }
    )
