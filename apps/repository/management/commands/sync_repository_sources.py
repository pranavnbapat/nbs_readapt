from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Validate registered Excel sources, import them into PostgreSQL, and rebuild the OpenSearch index."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input-dir",
            default=str(settings.INITIAL_INPUT_DIR),
            help="Directory containing registered Excel source files.",
        )
        parser.add_argument(
            "--dataset",
            action="append",
            default=[],
            help="Limit the sync to one or more dataset keys from the source registry.",
        )
        parser.add_argument(
            "--filename",
            action="append",
            default=[],
            help="Limit the sync to one or more registered filenames.",
        )
        parser.add_argument(
            "--skip-validate",
            action="store_true",
            help="Skip validation before importing.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously imported repository data before importing.",
        )

    def handle(self, *args, **options):
        input_dir = Path(options["input_dir"])
        if not input_dir.exists():
            raise CommandError(f"Input directory does not exist: {input_dir}")

        datasets = options["dataset"]
        filenames = options["filename"]

        if not options["skip_validate"]:
            call_command(
                "validate_repository_sources",
                input_dir=str(input_dir),
                dataset=datasets,
                filename=filenames,
            )

        call_command(
            "import_repository_sources",
            input_dir=str(input_dir),
            dataset=datasets,
            filename=filenames,
            source_label="operator_sync",
            notes="Operator-triggered sync from registered Excel sources",
            reset=options["reset"],
        )
        call_command("index_repository_records", recreate=True)
