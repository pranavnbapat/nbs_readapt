from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.repository.services import InitialInputImporter
from apps.repository.source_specs import get_source_specs, resolve_source_specs


class Command(BaseCommand):
    help = "Import registered repository Excel sources into PostgreSQL."

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
            help="Limit import to one or more dataset keys from the source registry.",
        )
        parser.add_argument(
            "--filename",
            action="append",
            default=[],
            help="Limit import to one or more registered filenames.",
        )
        parser.add_argument(
            "--source-label",
            default="initial_input",
            help="Label stored on the resulting import batch.",
        )
        parser.add_argument(
            "--notes",
            default="Import from registered Excel source specifications",
            help="Free-text notes stored on the resulting import batch.",
        )
        parser.add_argument(
            "--list-sources",
            action="store_true",
            help="Show the currently registered source specifications and exit.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously imported repository data before importing.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["list_sources"]:
            for spec in get_source_specs():
                self.stdout.write(
                    f"{spec.dataset}\t{spec.filename}\t{spec.sheet_name}\t{spec.normalizer_key}"
                )
            return

        input_dir = Path(options["input_dir"])
        if not input_dir.exists():
            raise CommandError(f"Input directory does not exist: {input_dir}")

        specs = resolve_source_specs(
            datasets=options["dataset"],
            filenames=options["filename"],
        )
        if not specs:
            raise CommandError("No source specifications matched the provided filters.")

        importer = InitialInputImporter(input_dir=input_dir)
        try:
            batch = importer.import_all(
                reset=options["reset"],
                specs=specs,
                source_label=options["source_label"],
                notes=options["notes"],
            )
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {batch.records_imported} records from {input_dir} into batch {batch.id}."
            )
        )
