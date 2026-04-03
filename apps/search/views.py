from __future__ import annotations

from typing import Any

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .opensearch import get_opensearch_client


def _list_param(request, name: str) -> list[str]:
    return [value for value in request.GET.getlist(name) if value]


def _build_filter_clauses(request) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = []

    keyword_filters = {
        "source_dataset": "source_dataset",
        "country": "countries",
        "geography_type": "geography_type",
        "hazard": "all_hazards",
        "nbs_type": "all_nbs_types",
        "implementation_stage": "implementation_stage",
        "policy_level": "policy_level",
    }
    for param, field in keyword_filters.items():
        values = _list_param(request, param)
        if values:
            filters.append({"terms": {field: values}})

    year_gte = request.GET.get("year_gte")
    year_lte = request.GET.get("year_lte")
    if year_gte or year_lte:
        year_range: dict[str, Any] = {}
        if year_gte:
            year_range["gte"] = int(year_gte)
        if year_lte:
            year_range["lte"] = int(year_lte)
        filters.append({"range": {"source_year": year_range}})

    return filters


@require_GET
def search_status_view(request):
    return JsonResponse(
        {
            "module": "search",
            "status": "ready_for_indexing",
            "opensearch_url": settings.OPENSEARCH["url"],
            "bm25_index": settings.OPENSEARCH["index_bm25"],
            "neural_index": settings.OPENSEARCH["index_neural"],
        }
    )


@require_GET
def search_query_view(request):
    q = (request.GET.get("q") or "").strip()
    size = min(int(request.GET.get("size", 20)), 100)
    filters = _build_filter_clauses(request)

    client = get_opensearch_client()
    body: dict[str, Any] = {
        "size": size,
        "_source": True,
        "query": {
            "bool": {
                "filter": filters,
                "must": [],
            }
        },
        "sort": ["_score", {"source_year": {"order": "desc", "missing": "_last"}}],
    }

    if q:
        body["query"]["bool"]["must"].append(
            {
                "multi_match": {
                    "query": q,
                    "fields": [
                        "title^5",
                        "search_text^3",
                        "keywords^2",
                        "abstract^2",
                        "summary^2",
                        "description",
                    ],
                    "type": "best_fields",
                    "operator": "or",
                }
            }
        )
    else:
        body["query"]["bool"]["must"].append({"match_all": {}})

    response = client.search(index=settings.OPENSEARCH["index_bm25"], body=body)
    hits = []
    for hit in response.get("hits", {}).get("hits", []):
        source = hit.get("_source", {})
        hits.append({"id": hit.get("_id"), "score": hit.get("_score"), **source})

    return JsonResponse(
        {
            "took_ms": response.get("took"),
            "total": response.get("hits", {}).get("total", {}).get("value", 0),
            "hits": hits,
        }
    )


@require_GET
def search_facets_view(request):
    q = (request.GET.get("q") or "").strip()
    filters = _build_filter_clauses(request)

    client = get_opensearch_client()
    must_clause: list[dict[str, Any]] = [{"match_all": {}}]
    if q:
        must_clause = [
            {
                "multi_match": {
                    "query": q,
                    "fields": [
                        "title^5",
                        "search_text^3",
                        "keywords^2",
                        "abstract^2",
                        "summary^2",
                        "description",
                    ],
                    "type": "best_fields",
                    "operator": "or",
                }
            }
        ]

    body = {
        "size": 0,
        "query": {
            "bool": {
                "filter": filters,
                "must": must_clause,
            }
        },
        "aggs": {
            "source_dataset": {"terms": {"field": "source_dataset", "size": 20}},
            "countries": {"terms": {"field": "countries", "size": 100}},
            "geography_type": {"terms": {"field": "geography_type", "size": 20}},
            "all_hazards": {"terms": {"field": "all_hazards", "size": 100}},
            "all_nbs_types": {"terms": {"field": "all_nbs_types", "size": 100}},
            "implementation_stage": {"terms": {"field": "implementation_stage", "size": 50}},
            "policy_level": {"terms": {"field": "policy_level", "size": 50}},
            "year_min": {"min": {"field": "source_year"}},
            "year_max": {"max": {"field": "source_year"}},
        },
    }
    response = client.search(index=settings.OPENSEARCH["index_bm25"], body=body)
    aggs = response.get("aggregations", {})

    def buckets(name: str):
        return [{"key": bucket["key"], "doc_count": bucket["doc_count"]} for bucket in aggs.get(name, {}).get("buckets", [])]

    return JsonResponse(
        {
            "source_dataset": buckets("source_dataset"),
            "countries": buckets("countries"),
            "geography_type": buckets("geography_type"),
            "hazards": buckets("all_hazards"),
            "nbs_types": buckets("all_nbs_types"),
            "implementation_stage": buckets("implementation_stage"),
            "policy_level": buckets("policy_level"),
            "year_min": aggs.get("year_min", {}).get("value"),
            "year_max": aggs.get("year_max", {}).get("value"),
        }
    )
