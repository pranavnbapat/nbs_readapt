from __future__ import annotations

from typing import Any

from apps.repository.models import RepositoryRecord


SUPRANATIONAL_LABELS = {"European Union", "Europe"}
GLOBAL_LABELS = {"Global"}


def build_record_search_text(record: RepositoryRecord) -> str:
    parts = [
        record.title,
        record.source_database,
        record.record_subtype,
        record.document_type,
        record.policy_level,
        record.geographic_scope,
        record.territorial_context,
        record.environment_type,
        record.implementation_stage,
        record.community_engagement_level,
        record.authors,
        record.affiliations,
        record.acronym,
        record.funding_source,
        record.abstract,
        record.summary,
        record.description,
        record.objective,
        record.methods,
        record.outcomes_targeted,
        record.ecological_impacts,
        record.socio_economic_impacts,
        record.governance_insights,
        record.finance_insights,
        record.implementation_steps,
        record.monitoring_reporting,
        record.barriers,
        record.enablers,
        record.lessons,
        record.key_findings,
        record.enforcement_mechanisms,
        record.nbs_relevance,
        record.nbs_commitment,
        record.country_display,
        record.city_location,
        record.location_text,
        record.keywords,
    ]
    return "\n".join(part.strip() for part in parts if part and part.strip())


def build_geography_metadata(record: RepositoryRecord, countries: list[str]) -> dict[str, str]:
    country_display = (record.country_display or "").strip()
    geographic_scope = (record.geographic_scope or "").strip()
    city_location = (record.city_location or "").strip()

    label = country_display or geographic_scope or city_location or record.location_text or ""

    if label in GLOBAL_LABELS:
        geography_type = "global"
    elif label in SUPRANATIONAL_LABELS:
        geography_type = "supranational"
    elif len(countries) == 1:
        geography_type = "country"
    elif len(countries) > 1:
        geography_type = "multi_country"
    elif any(token in label for token in ["Basin", "Region", "Sea", "Space", "("]):
        geography_type = "transnational_region"
    elif city_location:
        geography_type = "local_place"
    else:
        geography_type = "unknown"

    return {
        "geography_type": geography_type,
        "geography_label": label,
        "geo_precision": str((record.normalized_payload or {}).get("geo_precision", "none")),
    }


def build_record_document(record: RepositoryRecord) -> dict[str, Any]:
    countries = list(record.countries.values_list("name", flat=True))
    primary_hazards = list(record.primary_hazards.values_list("name", flat=True))
    secondary_hazards = list(record.secondary_hazards.values_list("name", flat=True))
    primary_nbs_types = list(record.primary_nbs_types.values_list("name", flat=True))
    secondary_nbs_types = list(record.secondary_nbs_types.values_list("name", flat=True))

    source_year = record.publication_year or record.start_year or record.end_year
    geography = build_geography_metadata(record, countries)

    return {
        "record_id": record.id,
        "source_dataset": record.source_dataset,
        "source_sheet": record.source_sheet,
        "source_record_id": record.source_record_id,
        "title": record.title,
        "source_database": record.source_database,
        "record_subtype": record.record_subtype,
        "document_type": record.document_type,
        "policy_level": record.policy_level,
        "geographic_scope": record.geographic_scope,
        "territorial_context": record.territorial_context,
        "environment_type": record.environment_type,
        "implementation_stage": record.implementation_stage,
        "community_engagement_level": record.community_engagement_level,
        "data_availability": record.data_availability,
        "publication_year": record.publication_year,
        "start_year": record.start_year,
        "end_year": record.end_year,
        "source_year": source_year,
        "lead_organization": record.lead_organization,
        "authors": record.authors,
        "affiliations": record.affiliations,
        "acronym": record.acronym,
        "funding_source": record.funding_source,
        "funding_contribution": record.funding_contribution,
        "doi": record.doi,
        "source_url": record.source_url,
        "source_url_secondary": record.source_url_secondary,
        "abstract": record.abstract,
        "summary": record.summary,
        "description": record.description,
        "objective": record.objective,
        "methods": record.methods,
        "outcomes_targeted": record.outcomes_targeted,
        "ecological_impacts": record.ecological_impacts,
        "socio_economic_impacts": record.socio_economic_impacts,
        "governance_insights": record.governance_insights,
        "finance_insights": record.finance_insights,
        "implementation_steps": record.implementation_steps,
        "monitoring_reporting": record.monitoring_reporting,
        "barriers": record.barriers,
        "enablers": record.enablers,
        "lessons": record.lessons,
        "key_findings": record.key_findings,
        "enforcement_mechanisms": record.enforcement_mechanisms,
        "nbs_relevance": record.nbs_relevance,
        "nbs_commitment": record.nbs_commitment,
        "country_display": record.country_display,
        "city_location": record.city_location,
        "location_text": record.location_text,
        "latitude": record.latitude,
        "longitude": record.longitude,
        **geography,
        "keywords": record.keywords,
        "countries": countries,
        "primary_hazards": primary_hazards,
        "secondary_hazards": secondary_hazards,
        "primary_nbs_types": primary_nbs_types,
        "secondary_nbs_types": secondary_nbs_types,
        "all_hazards": sorted(set(primary_hazards + secondary_hazards)),
        "all_nbs_types": sorted(set(primary_nbs_types + secondary_nbs_types)),
        "search_text": build_record_search_text(record),
    }


def build_index_body() -> dict[str, Any]:
    keyword_fields = [
        "source_dataset",
        "source_sheet",
        "source_record_id",
        "source_database",
        "record_subtype",
        "document_type",
        "policy_level",
        "geographic_scope",
        "territorial_context",
        "environment_type",
        "implementation_stage",
        "community_engagement_level",
        "data_availability",
        "lead_organization",
        "acronym",
        "funding_source",
        "doi",
        "geography_type",
        "geography_label",
        "geo_precision",
    ]
    body = {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            }
        },
        "mappings": {
            "dynamic": False,
            "properties": {
                "record_id": {"type": "integer"},
                "title": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 512}}},
                "search_text": {"type": "text"},
                "authors": {"type": "text"},
                "affiliations": {"type": "text"},
                "abstract": {"type": "text"},
                "summary": {"type": "text"},
                "description": {"type": "text"},
                "objective": {"type": "text"},
                "methods": {"type": "text"},
                "outcomes_targeted": {"type": "text"},
                "ecological_impacts": {"type": "text"},
                "socio_economic_impacts": {"type": "text"},
                "governance_insights": {"type": "text"},
                "finance_insights": {"type": "text"},
                "implementation_steps": {"type": "text"},
                "monitoring_reporting": {"type": "text"},
                "barriers": {"type": "text"},
                "enablers": {"type": "text"},
                "lessons": {"type": "text"},
                "key_findings": {"type": "text"},
                "enforcement_mechanisms": {"type": "text"},
                "nbs_relevance": {"type": "text"},
                "nbs_commitment": {"type": "text"},
                "country_display": {"type": "text"},
                "city_location": {"type": "text"},
                "location_text": {"type": "text"},
                "keywords": {"type": "text"},
                "publication_year": {"type": "integer"},
                "start_year": {"type": "integer"},
                "end_year": {"type": "integer"},
                "source_year": {"type": "integer"},
                "latitude": {"type": "float"},
                "longitude": {"type": "float"},
                "countries": {"type": "keyword"},
                "primary_hazards": {"type": "keyword"},
                "secondary_hazards": {"type": "keyword"},
                "all_hazards": {"type": "keyword"},
                "primary_nbs_types": {"type": "keyword"},
                "secondary_nbs_types": {"type": "keyword"},
                "all_nbs_types": {"type": "keyword"},
            },
        },
    }
    for field in keyword_fields:
        body["mappings"]["properties"][field] = {"type": "keyword"}
    return body
