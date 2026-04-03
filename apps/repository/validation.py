from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .source_specs import SourceSpec


@dataclass
class SourceValidationResult:
    dataset: str
    filename: str
    sheet_name: str
    status: str
    row_count: int
    column_count: int
    source_id_column: str
    duplicate_source_ids: int
    missing_required_columns: list[str]
    available_columns: list[str]
    messages: list[str]


class RepositorySourceValidator:
    def __init__(self, input_dir: Path):
        self.input_dir = input_dir

    def validate_specs(self, specs: list[SourceSpec]) -> list[SourceValidationResult]:
        return [self.validate_spec(spec) for spec in specs]

    def validate_spec(self, spec: SourceSpec) -> SourceValidationResult:
        file_path = self.input_dir / spec.filename
        if not file_path.exists():
            return SourceValidationResult(
                dataset=spec.dataset,
                filename=spec.filename,
                sheet_name=spec.sheet_name,
                status="error",
                row_count=0,
                column_count=0,
                source_id_column=spec.source_id_column,
                duplicate_source_ids=0,
                missing_required_columns=[],
                available_columns=[],
                messages=[f"Missing file: {file_path}"],
            )

        try:
            dataframe = pd.read_excel(file_path, sheet_name=spec.sheet_name)
        except ValueError as exc:
            return SourceValidationResult(
                dataset=spec.dataset,
                filename=spec.filename,
                sheet_name=spec.sheet_name,
                status="error",
                row_count=0,
                column_count=0,
                source_id_column=spec.source_id_column,
                duplicate_source_ids=0,
                missing_required_columns=[],
                available_columns=[],
                messages=[f"Worksheet error: {exc}"],
            )
        except Exception as exc:
            return SourceValidationResult(
                dataset=spec.dataset,
                filename=spec.filename,
                sheet_name=spec.sheet_name,
                status="error",
                row_count=0,
                column_count=0,
                source_id_column=spec.source_id_column,
                duplicate_source_ids=0,
                missing_required_columns=[],
                available_columns=[],
                messages=[f"Read error: {exc}"],
            )

        columns = [str(column) for column in dataframe.columns]
        missing_required = [column for column in spec.required_columns if column not in dataframe.columns]
        duplicate_count = 0
        messages: list[str] = []

        if spec.source_id_column not in dataframe.columns:
            missing_required = sorted(set(missing_required + [spec.source_id_column]))
        else:
            source_ids = dataframe[spec.source_id_column].dropna().astype(str).str.strip()
            source_ids = source_ids[source_ids != ""]
            duplicate_count = int(source_ids.duplicated().sum())
            if duplicate_count:
                messages.append(f"{duplicate_count} duplicated source IDs detected in {spec.source_id_column}.")

        if missing_required:
            messages.append(f"Missing required columns: {', '.join(missing_required)}")

        if not messages:
            messages.append("Validation passed.")

        status = "error" if missing_required else "warning" if duplicate_count else "ok"

        return SourceValidationResult(
            dataset=spec.dataset,
            filename=spec.filename,
            sheet_name=spec.sheet_name,
            status=status,
            row_count=len(dataframe.index),
            column_count=len(columns),
            source_id_column=spec.source_id_column,
            duplicate_source_ids=duplicate_count,
            missing_required_columns=missing_required,
            available_columns=columns,
            messages=messages,
        )
