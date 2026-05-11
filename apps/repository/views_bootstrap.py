from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from apps.search.opensearch import get_opensearch_client


DATASET_TO_TYPE = {
    "papers": "Scientific Paper",
    "network_projects": "Case Study",
    "eu_projects": "EU Project",
    "policies": "EU Policy",
}

DATASET_PREFIX = {
    "papers": "Pap",
    "network_projects": "Cas",
    "eu_projects": "Eup",
    "policies": "Pol",
}

NBS_PALETTE = ["#059669", "#0D9488", "#7C3AED", "#D97706", "#0284C7", "#DC2626", "#65BF85", "#82B82A"]
HAZ_PALETTE = ["#0284C7", "#EA580C", "#0D9488", "#D97706", "#DC2626", "#059669", "#7C3AED", "#64748B", "#94A3B8"]


# Map raw data hazard names to the prototype's canonical 6+ labels.
HAZARD_MAP = {
    "flooding": "Flooding",
    "extreme temperature events": "Heat/Extreme Temperature",
    "heat/extreme temperature": "Heat/Extreme Temperature",
    "heat": "Heat/Extreme Temperature",
    "precipitation extremes and drought": "Drought",
    "drought": "Drought",
    "sea level rise and coastal change": "Sea-Level Rise&Coastal",
    "sea-level rise&coastal": "Sea-Level Rise&Coastal",
    "sea-level rise & coastal": "Sea-Level Rise&Coastal",
    "wildfires": "Wildfire",
    "wildfire": "Wildfire",
    "biological hazards": "Biological Hazards",
    "oceanic change": "Oceanic Change",
    "cryosphere change": "Cryosphere Change",
    "storms and cyclones": "Storms&Cyclones",
    "storms&cyclones": "Storms&Cyclones",
}

TERRITORY_MAP = {
    "urban": "Urban",
    "rural": "Rural",
    "regional": "Regional",
    "national": "National",
    "multi": "Multi-scale",
    "multi-scale": "Multi-scale",
}

SCALE_MAP = {
    "city": "City",
    "regional": "Regional",
    "region": "Regional",
    "national": "National",
    "site": "Site",
    "neighbourhood": "Neighbourhood",
    "neighborhood": "Neighbourhood",
}


def _normalize(value: str, mapping: dict[str, str]) -> str:
    """Pick the first semicolon-separated part that maps to a canonical label."""
    if not value:
        return ""
    for part in value.split(";"):
        canonical = mapping.get(part.strip().lower())
        if canonical:
            return canonical
    return value.split(";")[0].strip()


def _assign_palette(counter: Counter[str], palette: list[str]) -> dict[str, str]:
    """Assign a color to each label, ordered by frequency desc."""
    return {label: palette[i % len(palette)] for i, (label, _) in enumerate(counter.most_common())}


def _shape_record(src: dict[str, Any]) -> dict[str, Any]:
    """Map an OpenSearch _source doc to the prototype's short-key record shape."""
    dataset = src.get("source_dataset") or ""
    nbs_types = src.get("all_nbs_types") or []
    hazards = src.get("all_hazards") or []
    countries = src.get("countries") or []
    country = src.get("country_display") or (countries[0] if countries else "")
    year = src.get("source_year")
    record_id = src.get("source_record_id") or str(src.get("record_id") or "")
    prefix = DATASET_PREFIX.get(dataset, "Rec")
    rec_id = record_id if record_id.startswith(prefix) else f"{prefix}_{record_id}"

    raw_hz = hazards[0] if hazards else ""
    raw_te = src.get("territorial_context") or ""
    # Scale can live in policy_level or geographic_scope; prefer whichever has a mappable value.
    raw_sc = src.get("policy_level") or src.get("geographic_scope") or ""
    sc_value = _normalize(raw_sc, SCALE_MAP)
    if sc_value == raw_sc.split(";")[0].strip():  # no mapping hit on first field
        alt = src.get("geographic_scope") if src.get("policy_level") else src.get("policy_level")
        if alt:
            alt_value = _normalize(alt, SCALE_MAP)
            # Use the alt only if it produced a known canonical label
            if alt_value in SCALE_MAP.values():
                sc_value = alt_value

    return {
        "id": rec_id,
        "ty": DATASET_TO_TYPE.get(dataset, dataset),
        "ti": src.get("title") or "",
        "so": src.get("source_database") or "",
        "yr": str(year) if year else "",
        "co": country,
        "nb": nbs_types[0] if nbs_types else "",
        "hz": HAZARD_MAP.get(raw_hz.strip().lower(), raw_hz),
        "te": _normalize(raw_te, TERRITORY_MAP),
        "sc": sc_value,
        "im": src.get("implementation_stage") or "",
        "ce": src.get("community_engagement_level") or "",
        "ba": src.get("barriers") or "",
        "en": src.get("enablers") or "",
        "le": src.get("lessons") or "",
        "do": src.get("doi") or src.get("source_url") or "",
        "su": src.get("summary") or src.get("abstract") or "",
        "lg": src.get("document_type") or "",
        "la": src.get("latitude"),
        "ln": src.get("longitude"),
        "ci": src.get("city_location") or "",
    }


def _shape_pin(rec: dict[str, Any]) -> dict[str, Any]:
    """A pin is the geolocated subset of fields used by the map."""
    return {
        "t": rec["ti"],
        "ci": rec["ci"],
        "co": rec["co"],
        "la": rec["la"],
        "ln": rec["ln"],
        "nb": rec["nb"],
        "hz": rec["hz"],
        "ty": rec["ty"],
        "yr": rec["yr"],
        "le": (rec["le"] or "")[:100],
        "so": rec["so"],
    }


def _compute_analytics(records: list[dict[str, Any]]) -> dict[str, Any]:
    type_counts: Counter[str] = Counter()
    nbs_counts: Counter[str] = Counter()
    haz_counts: Counter[str] = Counter()
    ter_counts: Counter[str] = Counter()
    sca_counts: Counter[str] = Counter()
    imp_counts: Counter[str] = Counter()
    year_counts: Counter[str] = Counter()
    country_counts: Counter[str] = Counter()
    by_country_nbs: dict[str, Counter[str]] = defaultdict(Counter)
    by_country_haz: dict[str, Counter[str]] = defaultdict(Counter)
    by_country_ter: dict[str, Counter[str]] = defaultdict(Counter)
    by_country_type: dict[str, Counter[str]] = defaultdict(Counter)
    by_country_coords: dict[str, int] = defaultdict(int)
    with_coords = 0

    for rec in records:
        has_coords = rec["la"] is not None and rec["ln"] is not None
        if has_coords:
            with_coords += 1
        if rec["ty"]:
            type_counts[rec["ty"]] += 1
        if rec["nb"]:
            nbs_counts[rec["nb"]] += 1
        if rec["hz"]:
            haz_counts[rec["hz"]] += 1
        if rec["te"]:
            ter_counts[rec["te"]] += 1
        if rec["sc"]:
            sca_counts[rec["sc"]] += 1
        if rec["im"]:
            imp_counts[rec["im"]] += 1
        if rec["yr"]:
            year_counts[rec["yr"]] += 1
        co = rec["co"]
        if co:
            country_counts[co] += 1
            if has_coords:
                by_country_coords[co] += 1
            if rec["nb"]:
                by_country_nbs[co][rec["nb"]] += 1
            if rec["hz"]:
                by_country_haz[co][rec["hz"]] += 1
            if rec["te"]:
                by_country_ter[co][rec["te"]] += 1
            if rec["ty"]:
                by_country_type[co][rec["ty"]] += 1

    country_stats = {
        co: {
            "count": cnt,
            "with_coords": by_country_coords[co],
            "nbs": by_country_nbs[co].most_common(),
            "hazard": by_country_haz[co].most_common(),
            "territory": by_country_ter[co].most_common(),
            "types": by_country_type[co].most_common(),
        }
        for co, cnt in country_counts.most_common()
    }

    return {
        "total": len(records),
        "with_coords": with_coords,
        "type_counts": dict(type_counts),
        "nbs_counts": nbs_counts.most_common(),
        "haz_counts": haz_counts.most_common(),
        "territory_counts": ter_counts.most_common(),
        "scale_counts": sca_counts.most_common(),
        "impl_counts": imp_counts.most_common(),
        "year_counts": sorted(year_counts.items()),
        "country_list": list(country_counts.keys()),
        "country_stats": country_stats,
        "nbs_colors": _assign_palette(nbs_counts, NBS_PALETTE),
        "haz_colors": _assign_palette(haz_counts, HAZ_PALETTE),
    }


@require_GET
@cache_page(60 * 5)
def bootstrap_view(request):
    """Return all repository records shaped for the prototype frontend."""
    records: list[dict[str, Any]] = []
    error: str | None = None
    raw_sources: list[dict[str, Any]] = []

    try:
        client = get_opensearch_client()
        index = settings.OPENSEARCH["index_bm25"]
        response = client.search(
            index=index,
            body={"size": 10000, "query": {"match_all": {}}, "_source": True},
        )
        for hit in response.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            raw_sources.append(src)
            records.append(_shape_record(src))
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"

    pins = [_shape_pin(r) for r in records if r["la"] is not None and r["ln"] is not None]
    analytics = _compute_analytics(records)

    # Diagnostics: show top distinct values for fields that might contain scale data
    if request.GET.get("debug"):
        scale_candidates = ("policy_level", "geographic_scope", "record_subtype", "environment_type")
        analytics["field_samples"] = {
            field: Counter((s.get(field) or "").strip() for s in raw_sources if (s.get(field) or "").strip()).most_common(15)
            for field in scale_candidates
        }

    payload: dict[str, Any] = {"records": records, "pins": pins, "analytics": analytics}
    if error:
        payload["error"] = error
    return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
