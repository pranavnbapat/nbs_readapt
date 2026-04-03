from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.repository.source_specs import resolve_source_specs
from apps.repository.validation import RepositorySourceValidator


class Command(BaseCommand):
    help = "Validate registered repository Excel sources before import."

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
            help="Limit validation to one or more dataset keys from the source registry.",
        )
        parser.add_argument(
            "--filename",
            action="append",
            default=[],
            help="Limit validation to one or more registered filenames.",
        )

    def handle(self, *args, **options):
        input_dir = Path(options["input_dir"])
        if not input_dir.exists():
            raise CommandError(f"Input directory does not exist: {input_dir}")

        specs = resolve_source_specs(
            datasets=options["dataset"],
            filenames=options["filename"],
        )
        if not specs:
            raise CommandError("No source specifications matched the provided filters.")

        validator = RepositorySourceValidator(input_dir=input_dir)
        results = validator.validate_specs(specs)

        worst_status = "ok"
        for result in results:
            if result.status == "error":
                worst_status = "error"
            elif result.status == "warning" and worst_status == "ok":
                worst_status = "warning"

            self.stdout.write(
                f"[{result.status.upper()}] {result.dataset} | {result.filename} | "
                f"rows={result.row_count} cols={result.column_count} duplicate_ids={result.duplicate_source_ids}"
            )
            for message in result.messages:
                self.stdout.write(f"  - {message}")

        if worst_status == "error":
            raise CommandError("Repository source validation failed.")
        if worst_status == "warning":
            self.stdout.write(self.style.WARNING("Repository source validation completed with warnings."))
        else:
            self.stdout.write(self.style.SUCCESS("Repository source validation passed."))
