from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from django.utils import timezone
from django.utils.text import slugify

from .models import Country, Hazard, ImportBatch, NbsType, RepositoryRecord
from .source_specs import SOURCE_SPECS, SourceSpec


COORDINATE_PATTERN = re.compile(r"(?P<label>.*?)\(\s*(?P<lat>-?\d+(?:\.\d+)?)\s*,\s*(?P<lon>-?\d+(?:\.\d+)?)\s*\)")

COUNTRY_CODE_TO_NAME = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "CH": "Switzerland",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DE": "Germany",
    "DK": "Denmark",
    "EE": "Estonia",
    "ES": "Spain",
    "EU": "European Union",
    "FI": "Finland",
    "FR": "France",
    "GR": "Greece",
    "HR": "Croatia",
    "HU": "Hungary",
    "IE": "Ireland",
    "IS": "Iceland",
    "IT": "Italy",
    "LI": "Liechtenstein",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "MT": "Malta",
    "NL": "Netherlands",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SE": "Sweden",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "UK": "United Kingdom",
}

COUNTRY_CENTROIDS = {
    "Austria": (47.5162, 14.5501),
    "Belgium": (50.5039, 4.4699),
    "Bulgaria": (42.7339, 25.4858),
    "Croatia": (45.1000, 15.2000),
    "Cyprus": (35.1264, 33.4299),
    "Czech Republic": (49.8175, 15.4730),
    "Denmark": (56.2639, 9.5018),
    "Estonia": (58.5953, 25.0136),
    "Finland": (61.9241, 25.7482),
    "France": (46.2276, 2.2137),
    "Germany": (51.1657, 10.4515),
    "Greece": (39.0742, 21.8243),
    "Hungary": (47.1625, 19.5033),
    "Iceland": (64.9631, -19.0208),
    "Ireland": (53.1424, -7.6921),
    "Italy": (41.8719, 12.5674),
    "Latvia": (56.8796, 24.6032),
    "Liechtenstein": (47.1660, 9.5554),
    "Lithuania": (55.1694, 23.8813),
    "Luxembourg": (49.8153, 6.1296),
    "Malta": (35.9375, 14.3754),
    "Netherlands": (52.1326, 5.2913),
    "Norway": (60.4720, 8.4689),
    "Poland": (51.9194, 19.1451),
    "Portugal": (39.3999, -8.2245),
    "Romania": (45.9432, 24.9668),
    "Slovakia": (48.6690, 19.6990),
    "Slovenia": (46.1512, 14.9955),
    "Spain": (40.4637, -3.7492),
    "Sweden": (60.1282, 18.6435),
    "Switzerland": (46.8182, 8.2275),
    "United Kingdom": (55.3781, -3.4360),
}

SUPRANATIONAL_NAMES = {"European Union", "Europe", "Global", "Multiple countries"}
NON_COUNTRY_LABEL_FRAGMENTS = (
    "europe",
    "european union",
    "eu member states",
    "all eu member states",
    "pan-european",
    "global",
    "multi-country",
    "region",
    "river basin",
    "basin",
    "north sea",
    "mediterranean",
    "caribbean",
    "trading partners",
    "showcases span",
    "continental",
    "member states",
)

COUNTRY_NAME_ALIASES = {
    "usa": "United States",
    "united states of america": "United States",
    "the netherlands": "Netherlands",
    "czechia": "Czech Republic",
    "russian federation": "Russia",
    "bosnia herzegovina": "Bosnia and Herzegovina",
    "cape verde": "Cape Verde",
    "south korea": "South Korea",
    "scotland (uk)": "United Kingdom",
    "southern france": "France",
    "martinique (france)": "Martinique",
}

CANONICAL_HAZARDS = [
    ("Flooding", ("flood", "pluvial", "stormwater", "runoff", "floodplain")),
    ("Extreme temperature events", ("heat", "temperature", "uhi", "urban heat", "heatwave", "heat stress", "cold")),
    ("Precipitation extremes and drought", ("drought", "water scarcity", "rainfall", "precipitation", "dry", "aridity")),
    ("Sea level rise and coastal change", ("sea level", "coastal", "shoreline", "storm surge", "salin", "erosion")),
    ("Storms and cyclones", ("storm", "cyclone", "hurricane", "windstorm")),
    ("Wildfires", ("wildfire", "fire regime", "fire risk", "mega-fire", "forest fire")),
    ("Biological hazards", ("biodiversity", "species", "pollinator", "pathogen", "disease", "pest", "vector", "vibrio", "biotic", "insect outbreak")),
    ("Oceanic change", ("ocean", "marine", "seagrass", "overfishing", "eutrophication", "acidification")),
    ("Cryosphere change", ("cryosphere", "glacial", "ice", "snow", "avalanche")),
    ("Land degradation", ("soil", "land degradation", "desertification", "land-use", "habitat fragmentation", "fragmentation")),
    ("Air pollution", ("air pollution", "air quality", "noise")),
]

CANONICAL_NBS_TYPES = [
    ("Green infrastructure", ("green infrastructure", "green spaces", "green roofs", "green walls", "street trees", "urban trees", "urban parks", "green corridors", "green facades", "urban green", "park", "healing gardens")),
    ("Blue infrastructure", ("blue infrastructure", "blue carbon", "marine", "river restoration", "freshwater", "coastal wetlands", "living shorelines", "seagrass", "mangrove", "salt marsh", "wetlands", "wetland", "pond", "lagoon", "intertidal", "reef")),
    ("Blue-green infrastructure", ("blue-green", "green-blue", "green/blue", "blue/green")),
    ("Hybrid and engineered NbS", ("hybrid", "engineered", "green-grey", "blue-grey", "grey-green", "grey / green", "dike", "barrier", "mobile flood barriers", "flood walls")),
    ("Ecosystem-based adaptation", ("ecosystem-based adaptation", "ecosystem based adaptation", "eba", "eco-drr", "ecosystem-based drr", "ecosystem-based forest management", "ecosystem-based water")),
    ("Nature based solutions general", ("nature based solutions", "nature-based solutions", "nbs", "urban nbs", "nature based adaptation", "nature-based engineering")),
    ("Ecological restoration", ("restoration", "rewilding", "renaturalisation", "renaturing", "reconnection", "rehabilitation", "free-flowing rivers")),
    ("Agroecological NbS", ("agroecolog", "agroforestry", "cover crops", "buffer strips", "hedgerows", "alley cropping", "crop diversification", "conservation agriculture")),
    ("Forest-based NbS", ("forest", "afforestation", "reforestation", "closer-to-nature forestry", "climate-smart forestry", "fire-adapted landscapes")),
    ("Natural water retention measures", ("natural water retention", "nwrs", "nwrm", "suds", "sustainable drainage", "bioswale", "bioretention", "rain gardens", "permeable pavement", "infiltration", "detention basin", "retention basin", "swales", "floodable parks", "low impact development", "lid")),
    ("Area-based conservation", ("protected areas", "conservation", "mpa", "marine protected areas", "area-based conservation")),
    ("Ecosystem services approach", ("ecosystem services", "ecosystem service", "natural capital", "valuation")),
]

INVALID_HAZARD_SUBSTRINGS = (
    "cross cutting lens",
    "blue infrastructure",
    "ecosystem based adaptation",
    "climate adaptation",
    "climate resilience",
    "adaptation/mitigation",
    "not hazard-specific",
    "general climate resilience",
    "indirect",
    "includes resilience aspects",
)

INVALID_NBS_SUBSTRINGS = (
    "eu cohesion",
    "eu life",
    "emfaf",
    "fund",
    "budget",
    "reserve",
    "revenue",
    "market",
    "capacity building",
    "knowledge",
    "governance",
    "justice-focused",
    "citizen science",
    "living labs",
    "co-creation",
    "monitoring",
    "valuation",
    "carbon credit",
    "dss",
)


def clean_value(value: Any) -> Any:
    if value is None:
        return None
    if pd.isna(value):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


def text_value(value: Any) -> str:
    cleaned = clean_value(value)
    return str(cleaned) if cleaned is not None else ""


def int_value(value: Any) -> int | None:
    cleaned = clean_value(value)
    if cleaned is None:
        return None
    try:
        return int(float(str(cleaned)))
    except (TypeError, ValueError):
        return None


def float_value(value: Any) -> float | None:
    cleaned = clean_value(value)
    if cleaned is None:
        return None
    try:
        return float(str(cleaned))
    except (TypeError, ValueError):
        return None


def split_multi_value(value: Any) -> list[str]:
    cleaned = text_value(value)
    if not cleaned:
        return []
    parts = re.split(r"\s*[;,]\s*", cleaned)
    return [part.strip() for part in parts if part.strip()]


def normalize_token(value: str) -> str:
    token = value.strip()
    token = token.replace("•", " ")
    token = token.replace("–", "-")
    token = re.sub(r"\s+", " ", token)
    token = re.sub(r"\s*\([^)]*$", "", token)
    token = token.strip(" -_,.;:/")
    return token


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def canonicalize_hazard(value: str) -> str | None:
    token = normalize_token(value)
    if not token:
        return None
    lowered = token.casefold()
    if lowered in {"unknown", "not applicable"}:
        return None
    if any(fragment in lowered for fragment in INVALID_HAZARD_SUBSTRINGS):
        return None
    for canonical, keywords in CANONICAL_HAZARDS:
        if any(keyword in lowered for keyword in keywords):
            return canonical
    if "climate change" in lowered or "climate risk" in lowered or "climate hazards" in lowered:
        return None
    return None


def canonicalize_nbs_type(value: str) -> str | None:
    token = normalize_token(value)
    if not token:
        return None
    lowered = token.casefold()
    if lowered in {"unknown", "general", "cross cutting lens"}:
        return None
    if any(fragment in lowered for fragment in INVALID_NBS_SUBSTRINGS):
        return None
    for canonical, keywords in CANONICAL_NBS_TYPES:
        if any(keyword in lowered for keyword in keywords):
            return canonical
    return None


def split_hazard_list(value: Any) -> list[str]:
    return dedupe_preserve_order(
        [canonical for token in split_multi_value(value) if (canonical := canonicalize_hazard(token))]
    )


def split_nbs_type_list(value: Any) -> list[str]:
    return dedupe_preserve_order(
        [canonical for token in split_multi_value(value) if (canonical := canonicalize_nbs_type(token))]
    )


def split_country_list(value: Any) -> list[str]:
    countries = []
    for token in split_multi_value(value):
        normalized = canonicalize_country_name(token)
        if normalized:
            countries.append(normalized)
    return dedupe_preserve_order(countries)


def normalize_country_code(value: Any) -> str:
    return text_value(value).upper()


def country_name_from_code(value: Any) -> str:
    return COUNTRY_CODE_TO_NAME.get(normalize_country_code(value), "")


def canonicalize_country_name(value: Any) -> str:
    token = normalize_token(text_value(value))
    if not token:
        return ""
    lowered = token.casefold()
    if any(fragment in lowered for fragment in NON_COUNTRY_LABEL_FRAGMENTS):
        return ""
    alias = COUNTRY_NAME_ALIASES.get(lowered)
    if alias:
        return alias
    if lowered in {name.casefold() for name in COUNTRY_CODE_TO_NAME.values()}:
        for name in COUNTRY_CODE_TO_NAME.values():
            if name.casefold() == lowered:
                return name
    return token


def is_country_name(value: str) -> bool:
    canonical = canonicalize_country_name(value)
    return canonical in COUNTRY_CENTROIDS or canonical in COUNTRY_CODE_TO_NAME.values()


def derive_country_display(*candidates: Any) -> tuple[str, str]:
    for source_name, value in candidates:
        text = text_value(value)
        if text:
            return canonicalize_country_display(text), source_name
    return "", ""


def canonicalize_country_display(value: str) -> str:
    if not value:
        return ""
    parts = split_multi_value(value)
    if len(parts) > 1:
        canonical_parts = [canonicalize_country_name(part) or normalize_token(part) for part in parts]
        canonical_parts = [part for part in canonical_parts if part]
        return " ; ".join(dedupe_preserve_order(canonical_parts))
    canonical = canonicalize_country_name(value)
    return canonical or normalize_token(value)


def derive_country_taxonomy(country_display: str, fallback_countries: list[str] | None = None) -> list[str]:
    countries = [country for country in (fallback_countries or []) if country and country not in SUPRANATIONAL_NAMES]
    if countries:
        return countries
    if not country_display:
        return []
    if " ; " in country_display:
        split_display = [canonicalize_country_name(part) for part in country_display.split(" ; ")]
        return dedupe_preserve_order([part for part in split_display if part])
    if is_country_name(country_display) and country_display not in SUPRANATIONAL_NAMES:
        return [canonicalize_country_name(country_display)]
    return []


def derive_country_centroid(country_display: str, latitude: float | None, longitude: float | None) -> tuple[float | None, float | None, str]:
    if latitude is not None and longitude is not None:
        return latitude, longitude, "source"
    centroid = COUNTRY_CENTROIDS.get(country_display)
    if centroid:
        return centroid[0], centroid[1], "country_centroid"
    return latitude, longitude, "none"


def parse_coordinate_blob(value: Any) -> tuple[str, float | None, float | None]:
    raw = text_value(value)
    if not raw:
        return "", None, None
    match = COORDINATE_PATTERN.search(raw)
    if not match:
        return raw, None, None
    label = match.group("label").strip(" ;")
    return raw, float(match.group("lat")), float(match.group("lon"))


def slug_get_or_create(model, name: str):
    normalized_name = name.strip()
    slug = slugify(normalized_name)
    if not slug:
        return model.objects.get_or_create(name=normalized_name)[0]

    existing = model.objects.filter(slug=slug).first()
    if existing:
        return existing

    return model.objects.create(name=normalized_name, slug=slug)


def row_to_payload(row: pd.Series) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in row.items():
        payload[str(key)] = clean_value(value)
    return payload


@dataclass
class NormalizedRecord:
    source_dataset: str
    source_sheet: str
    source_row_number: int
    source_uid: str
    source_record_id: str
    title: str
    data: dict[str, Any]
    countries: list[str]
    primary_hazards: list[str]
    secondary_hazards: list[str]
    primary_nbs_types: list[str]
    secondary_nbs_types: list[str]


class InitialInputImporter:
    def __init__(self, input_dir: Path):
        self.input_dir = input_dir

    def import_all(
        self,
        reset: bool = False,
        specs: list[SourceSpec] | None = None,
        source_label: str = "initial_input",
        notes: str = "Import from numbered Excel sources",
    ) -> ImportBatch:
        if reset:
            RepositoryRecord.objects.all().delete()
            Country.objects.all().delete()
            Hazard.objects.all().delete()
            NbsType.objects.all().delete()
            ImportBatch.objects.all().delete()

        selected_specs = specs or SOURCE_SPECS
        missing_files = [str(self.input_dir / spec.filename) for spec in selected_specs if not (self.input_dir / spec.filename).exists()]
        if missing_files:
            missing_display = ", ".join(missing_files)
            raise FileNotFoundError(f"Missing source files: {missing_display}")

        batch = ImportBatch.objects.create(source_label=source_label, notes=notes)
        imported_count = 0

        for spec in selected_specs:
            file_path = self.input_dir / spec.filename
            dataframe = pd.read_excel(file_path, sheet_name=spec.sheet_name)
            for row_index, (_, row) in enumerate(dataframe.iterrows(), start=1):
                normalized = self.normalize_row(spec=spec, row=row, row_index=row_index)
                self.upsert_record(batch=batch, record=normalized)
                imported_count += 1

        batch.records_imported = imported_count
        batch.completed_at = timezone.now()
        batch.save(update_fields=["records_imported", "completed_at", "updated_at"])
        return batch

    def normalize_row(self, spec: SourceSpec, row: pd.Series, row_index: int) -> NormalizedRecord:
        payload = row_to_payload(row)
        dataset = spec.dataset
        sheet_name = spec.sheet_name

        if spec.normalizer_key == "papers":
            location_text, latitude, longitude = parse_coordinate_blob(payload.get("City Location_Coordinates"))
            title = text_value(payload.get("Article_Title"))
            source_record_id = text_value(payload.get("PAPER_ID")) or f"{dataset}-{row_index}"
            country_display, country_display_source = derive_country_display(
                ("specific_countries_name", payload.get("Specific_Countries_Name")),
                ("geographic_focus", payload.get("Geographic focus")),
                ("case_study_name", payload.get("Case_Study_Name")),
            )
            countries = derive_country_taxonomy(country_display, split_country_list(payload.get("Specific_Countries_Name")))
            latitude, longitude, geo_precision = derive_country_centroid(country_display, latitude, longitude)
            data = {
                "source_database": text_value(payload.get("Database")),
                "record_subtype": "paper",
                "document_type": text_value(payload.get("Document_Type [JOURNAL_ARTICLE, CONFERENCE_PAPER, REPORT]")),
                "publication_year": int_value(payload.get("Publication_Year")),
                "authors": text_value(payload.get("Authors")),
                "affiliations": text_value(payload.get("Affiliations")),
                "doi": text_value(payload.get("DOI")),
                "abstract": text_value(payload.get("Abstract")),
                "objective": text_value(payload.get("Objective ")),
                "methods": text_value(payload.get("Study design/Method ")),
                "outcomes_targeted": text_value(payload.get("Outcomes targeted/Monitoring ")),
                "ecological_impacts": text_value(payload.get("Ecological Outcome/Impacts")),
                "socio_economic_impacts": text_value(payload.get("Socio-economic outcome/impact")),
                "governance_insights": text_value(payload.get("Governance insights ")),
                "finance_insights": text_value(payload.get("Finance insights")),
                "community_engagement_level": text_value(payload.get("Community engagement level ")),
                "barriers": text_value(payload.get("Barriers")),
                "enablers": text_value(payload.get("Enablers")),
                "lessons": text_value(payload.get("Lessons")),
                "data_availability": text_value(payload.get("Data availability")),
                "keywords": " ; ".join(
                    part for part in [text_value(payload.get("Keywords")), text_value(payload.get("Keywords_Database"))] if part
                ),
                "country_display": country_display,
                "city_location": text_value(payload.get("Case_Study_Name")),
                "location_text": location_text,
                "latitude": latitude,
                "longitude": longitude,
                "country_display_source": country_display_source,
                "geo_precision": geo_precision,
            }
            primary_hazards = split_hazard_list(payload.get("Climate hazard, primary"))
            secondary_hazards = split_hazard_list(payload.get("Climate hazard, secondary"))
            primary_nbs_types = split_nbs_type_list(payload.get("NBS Intervention type term"))
            secondary_nbs_types = split_nbs_type_list(payload.get("NbS_Type_Secondary"))
        elif spec.normalizer_key == "network_projects":
            location_text, latitude, longitude = parse_coordinate_blob(payload.get("City Location_Coordinates"))
            title = text_value(payload.get("Project_Title"))
            source_record_id = text_value(payload.get("ID_INT")) or f"{dataset}-{row_index}"
            country_display, country_display_source = derive_country_display(
                ("country_name", payload.get("Country_Name")),
                ("geographic_focus", payload.get("Geographic_Focus")),
                ("geographic_focus_alt", payload.get("Geographic focus")),
                ("city_location", payload.get("City_Location")),
            )
            countries = derive_country_taxonomy(country_display, split_country_list(payload.get("Country_Name")))
            latitude, longitude, geo_precision = derive_country_centroid(country_display, latitude, longitude)
            data = {
                "source_database": text_value(payload.get("Programme_Database")),
                "record_subtype": "network_project",
                "publication_year": int_value(payload.get("Starting_Year")),
                "lead_organization": text_value(payload.get("Coordinator")),
                "funding_source": text_value(payload.get("Funding_Source")),
                "funding_contribution": text_value(payload.get("Funding_Contribution")),
                "description": text_value(payload.get("Project_Description")),
                "environment_type": text_value(payload.get("Type_of_Environment")),
                "geographic_scope": text_value(payload.get("Geographic_Focus")) or text_value(payload.get("Geographic focus")),
                "territorial_context": text_value(payload.get("Territorial_Development_Context")),
                "community_engagement_level": text_value(payload.get("Community_Engagement")),
                "outcomes_targeted": text_value(payload.get("Outcomes_Targeted_or_Monitoring")),
                "ecological_impacts": text_value(payload.get("Ecological_Outcomes_or_Impacts")),
                "socio_economic_impacts": text_value(payload.get("Socio_Economic_Outcomes_or_Impacts")),
                "governance_insights": text_value(payload.get("Governance_Instruments")),
                "finance_insights": text_value(payload.get("Finance_Insights")),
                "barriers": text_value(payload.get("Barriers")),
                "enablers": text_value(payload.get("Enablers")),
                "lessons": text_value(payload.get("Scalability_or_Lessons")),
                "implementation_steps": text_value(payload.get("Implementation Design_Steps")),
                "implementation_stage": text_value(payload.get("Implementation_Stage")),
                "data_availability": text_value(payload.get("Data availability/FAIR")),
                "source_url": text_value(payload.get("Programme_Database_Link")),
                "country_display": country_display,
                "city_location": text_value(payload.get("City_Location")),
                "location_text": location_text,
                "latitude": latitude,
                "longitude": longitude,
                "country_display_source": country_display_source,
                "geo_precision": geo_precision,
                "keywords": " ; ".join(
                    part
                    for part in [
                        text_value(payload.get("Type_of_Approach_or_NbS_Concept")),
                        text_value(payload.get("Types_of_Societal_Challenges_Tackled")),
                        text_value(payload.get("Hazard_Evidence Observed ")),
                    ]
                    if part
                ),
            }
            primary_hazards = split_hazard_list(payload.get("Climate_Hazard_Primary"))
            secondary_hazards = split_hazard_list(payload.get("Climate_Hazard_Secondary"))
            primary_nbs_types = split_nbs_type_list(payload.get("NbS_Type_Primary"))
            secondary_nbs_types = split_nbs_type_list(payload.get("NbS_Type_Secondary"))
        elif spec.normalizer_key == "eu_projects":
            location_text, latitude, longitude = parse_coordinate_blob(payload.get("City Location_Coordinates"))
            title = text_value(payload.get("Project_Title"))
            source_record_id = text_value(payload.get("ID_INT")) or f"{dataset}-{row_index}"
            country_display, country_display_source = derive_country_display(
                ("country_name", payload.get("Country_Name")),
                ("geographic_focus", payload.get("Geographic focus")),
                ("city_location", payload.get("City_Location")),
            )
            countries = derive_country_taxonomy(country_display, split_country_list(payload.get("Country_Name")))
            latitude, longitude, geo_precision = derive_country_centroid(country_display, latitude, longitude)
            data = {
                "source_database": text_value(payload.get("Programme_Database")),
                "record_subtype": "eu_project",
                "publication_year": int_value(payload.get("Starting_Year")),
                "start_year": int_value(payload.get("Starting_Year")),
                "end_year": int_value(payload.get("End_Year")),
                "lead_organization": text_value(payload.get("Coordinator")),
                "acronym": text_value(payload.get("Acronym")),
                "funding_source": text_value(payload.get("Funding_Source")),
                "funding_contribution": text_value(payload.get("Funding_Contribution")),
                "description": text_value(payload.get("Project_Description")),
                "environment_type": text_value(payload.get("Type_of_Environment")),
                "geographic_scope": text_value(payload.get("Geographic focus")),
                "territorial_context": text_value(payload.get("Territorial_Development_Context")),
                "community_engagement_level": text_value(payload.get("Community_Engagement")),
                "outcomes_targeted": text_value(payload.get("Outcomes_Targeted_or_Monitoring")),
                "ecological_impacts": text_value(payload.get("Ecological_Outcomes_or_Impacts")),
                "socio_economic_impacts": text_value(payload.get("Socio_Economic_Outcomes_or_Impacts")),
                "governance_insights": text_value(payload.get("Governance_Instruments")),
                "finance_insights": text_value(payload.get("Finance_Insights")),
                "barriers": text_value(payload.get("Barriers")),
                "enablers": text_value(payload.get("Enablers")),
                "lessons": text_value(payload.get("Scalability_or_Lessons")),
                "implementation_steps": text_value(payload.get("Implementation Design_Steps")),
                "implementation_stage": text_value(payload.get("Implementation_Stage")),
                "data_availability": text_value(payload.get("Data availability/FAIR")),
                "source_url": text_value(payload.get("Project_Weblink")),
                "source_url_secondary": text_value(payload.get("Programme_Database_Link")),
                "country_display": country_display,
                "city_location": text_value(payload.get("City_Location")),
                "location_text": location_text,
                "latitude": latitude,
                "longitude": longitude,
                "country_display_source": country_display_source,
                "geo_precision": geo_precision,
                "keywords": " ; ".join(
                    part
                    for part in [
                        text_value(payload.get("Type_of_Approach_or_NbS_Concept")),
                        text_value(payload.get("Types_of_Societal_Challenges_Tackled")),
                        text_value(payload.get("Hazard_Evidence Observed ")),
                    ]
                    if part
                ),
            }
            primary_hazards = split_hazard_list(payload.get("Climate_Hazard_Primary"))
            secondary_hazards = split_hazard_list(payload.get("Climate_Hazard_Secondary"))
            primary_nbs_types = split_nbs_type_list(payload.get("NbS_Type_Primary"))
            secondary_nbs_types = split_nbs_type_list(payload.get("NbS_Type_Secondary"))
        else:
            title = text_value(payload.get("Document_Title"))
            source_record_id = text_value(payload.get("Record_ID")) or f"{dataset}-{row_index}"
            country_display, country_display_source = derive_country_display(
                ("country_name", payload.get("Country_Name")),
                ("country_code", country_name_from_code(payload.get("Country_Code"))),
                ("geographic_scope", payload.get("Geographic_Scope")),
            )
            countries = derive_country_taxonomy(
                country_display,
                split_country_list(payload.get("Country_Name")) or derive_country_taxonomy(country_name_from_code(payload.get("Country_Code"))),
            )
            latitude = float_value(payload.get("Lat"))
            longitude = float_value(payload.get("Lon"))
            latitude, longitude, geo_precision = derive_country_centroid(country_display, latitude, longitude)
            data = {
                "source_database": "policy_repository",
                "record_subtype": text_value(payload.get("Category of document (Law, Strategy, Regulation, Policy Document etc)")),
                "document_type": text_value(payload.get("Policy_Instrument_Type")),
                "policy_level": text_value(payload.get("Policy_Level")),
                "geographic_scope": text_value(payload.get("Geographic_Scope")),
                "territorial_context": text_value(payload.get("Territorial_Development_Context")),
                "environment_type": text_value(payload.get("Type_of_Environment")),
                "publication_year": int_value(payload.get("Year")),
                "lead_organization": text_value(payload.get("Issuing_Authority")),
                "source_url": text_value(payload.get("URL_Primary")),
                "source_url_secondary": text_value(payload.get("URL_Secondary")),
                "summary": text_value(payload.get("Summary of Relevance to NBS (Nature-Based Solutions)")),
                "nbs_relevance": text_value(payload.get("NbS_Relevance")),
                "nbs_commitment": text_value(payload.get("NbS_Target_or_Commitment")),
                "implementation_steps": text_value(payload.get("Implementation Measures")),
                "enforcement_mechanisms": text_value(payload.get("Enforcement Mechanisms")),
                "key_findings": text_value(payload.get("Key Findings / Insights")),
                "funding_source": text_value(payload.get("Funding_Mechanism")),
                "monitoring_reporting": text_value(payload.get("Monitoring_Reporting_Requirement")),
                "barriers": text_value(payload.get("Barriers")),
                "enablers": text_value(payload.get("Enablers")),
                "country_display": country_display,
                "city_location": text_value(payload.get("Country_Name")) or text_value(payload.get("Geographic_Scope")),
                "location_text": text_value(payload.get("Geographic_Scope")),
                "latitude": latitude,
                "longitude": longitude,
                "country_display_source": country_display_source,
                "geo_precision": geo_precision,
                "keywords": " ; ".join(
                    part
                    for part in [
                        text_value(payload.get("NbS Concept")),
                        text_value(payload.get("NBS Focus Strength")),
                        text_value(payload.get("Legal_Bindingness")),
                        text_value(payload.get("EU_Directive_or_Framework")),
                        text_value(payload.get("Governance_Instruments")),
                    ]
                    if part
                ),
            }
            primary_hazards = split_hazard_list(payload.get("Climate_Hazard_Primary"))
            secondary_hazards = split_hazard_list(payload.get("Climate_Hazard_Secondary"))
            primary_nbs_types = split_nbs_type_list(payload.get("NbS_Type_Primary"))
            secondary_nbs_types = []

        normalized_payload = {
            "countries": countries,
            "primary_hazards": primary_hazards,
            "secondary_hazards": secondary_hazards,
            "primary_nbs_types": primary_nbs_types,
            "secondary_nbs_types": secondary_nbs_types,
            "country_display_source": data.get("country_display_source", ""),
            "geo_precision": data.get("geo_precision", "none"),
        }

        source_uid = f"{dataset}:{sheet_name}:{row_index}"

        return NormalizedRecord(
            source_dataset=dataset,
            source_sheet=sheet_name,
            source_row_number=row_index,
            source_uid=source_uid,
            source_record_id=source_record_id,
            title=title,
            data={**data, "raw_payload": payload, "normalized_payload": normalized_payload},
            countries=countries,
            primary_hazards=primary_hazards,
            secondary_hazards=secondary_hazards,
            primary_nbs_types=primary_nbs_types,
            secondary_nbs_types=secondary_nbs_types,
        )

    def upsert_record(self, batch: ImportBatch, record: NormalizedRecord) -> RepositoryRecord:
        payload = record.data
        repository_record, _ = RepositoryRecord.objects.update_or_create(
            source_uid=record.source_uid,
            defaults={
                "import_batch": batch,
                "source_sheet": record.source_sheet,
                "source_dataset": record.source_dataset,
                "source_row_number": record.source_row_number,
                "title": record.title,
                "source_record_id": record.source_record_id,
                "source_database": payload.get("source_database", ""),
                "record_subtype": payload.get("record_subtype", ""),
                "document_type": payload.get("document_type", ""),
                "policy_level": payload.get("policy_level", ""),
                "geographic_scope": payload.get("geographic_scope", ""),
                "territorial_context": payload.get("territorial_context", ""),
                "environment_type": payload.get("environment_type", ""),
                "implementation_stage": payload.get("implementation_stage", ""),
                "community_engagement_level": payload.get("community_engagement_level", ""),
                "data_availability": payload.get("data_availability", ""),
                "publication_year": payload.get("publication_year"),
                "start_year": payload.get("start_year"),
                "end_year": payload.get("end_year"),
                "lead_organization": payload.get("lead_organization", ""),
                "authors": payload.get("authors", ""),
                "affiliations": payload.get("affiliations", ""),
                "acronym": payload.get("acronym", ""),
                "funding_source": payload.get("funding_source", ""),
                "funding_contribution": payload.get("funding_contribution", ""),
                "doi": payload.get("doi", ""),
                "source_url": payload.get("source_url", ""),
                "source_url_secondary": payload.get("source_url_secondary", ""),
                "abstract": payload.get("abstract", ""),
                "summary": payload.get("summary", ""),
                "description": payload.get("description", ""),
                "objective": payload.get("objective", ""),
                "methods": payload.get("methods", ""),
                "outcomes_targeted": payload.get("outcomes_targeted", ""),
                "ecological_impacts": payload.get("ecological_impacts", ""),
                "socio_economic_impacts": payload.get("socio_economic_impacts", ""),
                "governance_insights": payload.get("governance_insights", ""),
                "finance_insights": payload.get("finance_insights", ""),
                "implementation_steps": payload.get("implementation_steps", ""),
                "monitoring_reporting": payload.get("monitoring_reporting", ""),
                "barriers": payload.get("barriers", ""),
                "enablers": payload.get("enablers", ""),
                "lessons": payload.get("lessons", ""),
                "key_findings": payload.get("key_findings", ""),
                "enforcement_mechanisms": payload.get("enforcement_mechanisms", ""),
                "nbs_relevance": payload.get("nbs_relevance", ""),
                "nbs_commitment": payload.get("nbs_commitment", ""),
                "country_display": payload.get("country_display", ""),
                "city_location": payload.get("city_location", ""),
                "location_text": payload.get("location_text", ""),
                "latitude": payload.get("latitude"),
                "longitude": payload.get("longitude"),
                "keywords": payload.get("keywords", ""),
                "raw_payload": payload.get("raw_payload", {}),
                "normalized_payload": payload.get("normalized_payload", {}),
            },
        )

        repository_record.countries.set([slug_get_or_create(Country, name) for name in record.countries])
        repository_record.primary_hazards.set([slug_get_or_create(Hazard, name) for name in record.primary_hazards])
        repository_record.secondary_hazards.set([slug_get_or_create(Hazard, name) for name in record.secondary_hazards])
        repository_record.primary_nbs_types.set([slug_get_or_create(NbsType, name) for name in record.primary_nbs_types])
        repository_record.secondary_nbs_types.set([slug_get_or_create(NbsType, name) for name in record.secondary_nbs_types])
        return repository_record
