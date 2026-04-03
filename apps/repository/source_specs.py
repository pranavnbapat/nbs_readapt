from __future__ import annotations

from dataclasses import dataclass

from .models import RepositoryRecord


@dataclass(frozen=True)
class SourceSpec:
    filename: str
    dataset: str
    sheet_name: str
    normalizer_key: str
    source_id_column: str
    required_columns: tuple[str, ...]


SOURCE_SPECS = [
    SourceSpec(
        filename="01_Papers_Report.xlsx",
        dataset=RepositoryRecord.SourceDataset.PAPERS,
        sheet_name="Sheet1",
        normalizer_key="papers",
        source_id_column="PAPER_ID",
        required_columns=(
            "PAPER_ID",
            "Article_Title",
            "Publication_Year",
            "Specific_Countries_Name",
            "Climate hazard, primary",
            "NBS Intervention type term",
        ),
    ),
    SourceSpec(
        filename="02_Network_Projects.xlsx",
        dataset=RepositoryRecord.SourceDataset.NETWORK_PROJECTS,
        sheet_name="Sheet1",
        normalizer_key="network_projects",
        source_id_column="ID_INT",
        required_columns=(
            "ID_INT",
            "Project_Title",
            "Starting_Year",
            "Country_Name",
            "NbS_Type_Primary",
            "Climate_Hazard_Primary",
        ),
    ),
    SourceSpec(
        filename="03_EU Funded_Projects.xlsx",
        dataset=RepositoryRecord.SourceDataset.EU_PROJECTS,
        sheet_name="Sheet1",
        normalizer_key="eu_projects",
        source_id_column="ID_INT",
        required_columns=(
            "ID_INT",
            "Project_Title",
            "Starting_Year",
            "Country_Name",
            "NbS_Type_Primary",
            "Climate_Hazard_Primary",
        ),
    ),
    SourceSpec(
        filename="04_Policies.xlsx",
        dataset=RepositoryRecord.SourceDataset.POLICIES,
        sheet_name="NbS Policies",
        normalizer_key="policies",
        source_id_column="Record_ID",
        required_columns=(
            "Record_ID",
            "Document_Title",
            "Policy_Level",
            "Country_Name",
            "Year",
            "NbS_Type_Primary",
            "Climate_Hazard_Primary",
        ),
    ),
]


def get_source_specs() -> list[SourceSpec]:
    return list(SOURCE_SPECS)


def resolve_source_specs(
    datasets: list[str] | None = None,
    filenames: list[str] | None = None,
) -> list[SourceSpec]:
    dataset_filter = set(datasets or [])
    filename_filter = set(filenames or [])

    specs = []
    for spec in SOURCE_SPECS:
        if dataset_filter and spec.dataset not in dataset_filter:
            continue
        if filename_filter and spec.filename not in filename_filter:
            continue
        specs.append(spec)
    return specs
