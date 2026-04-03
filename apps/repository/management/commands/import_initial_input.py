from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.repository.services import InitialInputImporter


class Command(BaseCommand):
    help = "Import the numbered Excel files from initial_input into the repository schema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input-dir",
            default=str(settings.INITIAL_INPUT_DIR),
            help="Directory containing the numbered Excel input files.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously imported repository data before importing.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        input_dir = Path(options["input_dir"])
        if not input_dir.exists():
            raise CommandError(f"Input directory does not exist: {input_dir}")

        importer = InitialInputImporter(input_dir=input_dir)
        try:
            batch = importer.import_all(
                reset=options["reset"],
                source_label="initial_input",
                notes="Import from numbered Excel sources",
            )
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {batch.records_imported} records from {input_dir} into batch {batch.id}."
            )
        )
