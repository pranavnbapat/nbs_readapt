from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.repository.models import RepositoryRecord
from apps.search.opensearch import get_opensearch_client


class Command(BaseCommand):
    help = "Seed PostgreSQL and OpenSearch on first boot, based on actual repository state."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input-dir",
            default=str(settings.INITIAL_INPUT_DIR),
            help="Directory containing registered Excel source files.",
        )
        parser.add_argument(
            "--skip-validate",
            action="store_true",
            help="Skip Excel source validation before importing.",
        )
        parser.add_argument(
            "--force-import",
            action="store_true",
            help="Import repository sources even if PostgreSQL already has records.",
        )
        parser.add_argument(
            "--force-reindex",
            action="store_true",
            help="Recreate the OpenSearch index even if it already has documents.",
        )

    def handle(self, *args, **options):
        input_dir = Path(options["input_dir"])
        if not input_dir.exists():
            raise CommandError(f"Input directory does not exist: {input_dir}")

        record_count = RepositoryRecord.objects.count()
        should_import = options["force_import"] or record_count == 0

        if should_import:
            if not options["skip_validate"]:
                self.stdout.write("Validating repository Excel sources...")
                call_command("validate_repository_sources", input_dir=str(input_dir))

            import_verb = "Importing" if record_count == 0 else "Refreshing"
            self.stdout.write(f"{import_verb} repository data into PostgreSQL...")
            call_command(
                "import_repository_sources",
                input_dir=str(input_dir),
                source_label="bootstrap",
                notes="Automatic bootstrap import from registered Excel sources",
            )
            record_count = RepositoryRecord.objects.count()
            self.stdout.write(self.style.SUCCESS(f"PostgreSQL now contains {record_count} repository records."))
        else:
            self.stdout.write(f"PostgreSQL already contains {record_count} repository records; skipping import.")

        if record_count == 0:
            self.stdout.write("No repository records are present; skipping OpenSearch indexing.")
            return

        client = get_opensearch_client()
        index_name = settings.OPENSEARCH["index_bm25"]
        index_exists = client.indices.exists(index=index_name)
        doc_count = 0
        if index_exists:
            try:
                doc_count = int(client.count(index=index_name).get("count", 0))
            except Exception:
                doc_count = 0

        should_reindex = options["force_reindex"] or (not index_exists) or doc_count == 0
        if should_reindex:
            reason = "force requested"
            if not options["force_reindex"]:
                reason = "missing index" if not index_exists else "empty index"
            self.stdout.write(f"Rebuilding OpenSearch index ({reason})...")
            call_command("index_repository_records", recreate=True)
        else:
            self.stdout.write(f"OpenSearch index '{index_name}' already has {doc_count} documents; skipping reindex.")
