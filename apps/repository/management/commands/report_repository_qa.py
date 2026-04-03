from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.repository.qa import build_repository_qa_report


class Command(BaseCommand):
    help = "Generate a post-import QA report for repository data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input-dir",
            default=str(settings.INITIAL_INPUT_DIR),
            help="Directory containing registered Excel source files for validation comparison.",
        )
        parser.add_argument(
            "--batch-id",
            type=int,
            default=0,
            help="Optional import batch id to scope the report.",
        )
        parser.add_argument(
            "--output",
            default="",
            help="Optional JSON output file path.",
        )

    def handle(self, *args, **options):
        input_dir = Path(options["input_dir"])
        if not input_dir.exists():
            raise CommandError(f"Input directory does not exist: {input_dir}")

        report = build_repository_qa_report(
            input_dir=input_dir,
            batch_id=options["batch_id"] or None,
        )

        self.stdout.write(f"QA scope: {report['scope']}")
        self.stdout.write(f"Total records: {report['total_records']}")
        for item in report["import_vs_validation"]:
            self.stdout.write(
                f"- {item['dataset']}: validated={item['validated_row_count']} "
                f"imported={item['imported_record_count']} diff={item['difference']}"
            )
        self.stdout.write(
            "Field gaps: "
            + ", ".join(f"{key}={value}" for key, value in report["field_gaps"].items())
        )

        if options["output"]:
            output_path = Path(options["output"])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, default=str, indent=2), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Wrote QA report to {output_path}"))
