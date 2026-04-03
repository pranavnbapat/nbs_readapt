from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.repository.models import RepositoryRecord
from apps.search.indexing import build_record_document


class Command(BaseCommand):
    help = "Prepare OpenSearch-ready repository documents from PostgreSQL and export them as JSONL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="data/exports/opensearch_repository_documents.jsonl",
            help="Output path for the prepared JSONL documents.",
        )
        parser.add_argument(
            "--dataset",
            action="append",
            default=[],
            help="Limit preparation to one or more dataset keys.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Optional limit for inspection or QA runs.",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"])
        output_path.parent.mkdir(parents=True, exist_ok=True)

        queryset = (
            RepositoryRecord.objects.all()
            .prefetch_related(
                "countries",
                "primary_hazards",
                "secondary_hazards",
                "primary_nbs_types",
                "secondary_nbs_types",
            )
            .order_by("id")
        )
        if options["dataset"]:
            queryset = queryset.filter(source_dataset__in=options["dataset"])
        if options["limit"]:
            queryset = queryset[: options["limit"]]

        count = 0
        with output_path.open("w", encoding="utf-8") as handle:
            for record in queryset:
                handle.write(json.dumps(build_record_document(record), ensure_ascii=True))
                handle.write("\n")
                count += 1

        if count == 0:
            raise CommandError("No repository records matched the requested preparation scope.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Prepared {count} OpenSearch documents at {output_path}."
            )
        )
