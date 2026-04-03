from __future__ import annotations

from pathlib import Path

from django import forms
from django.conf import settings

from .source_specs import get_source_specs, resolve_source_specs


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)]


class RepositoryImportForm(forms.Form):
    datasets = forms.MultipleChoiceField(
        required=False,
        choices=[],
        help_text="Limit the import to selected registered datasets. Leave blank for all registered sources.",
        widget=forms.CheckboxSelectMultiple,
    )
    input_dir = forms.CharField(
        required=False,
        initial=str(settings.INITIAL_INPUT_DIR),
        help_text="Server-side directory containing registered Excel filenames.",
    )
    uploads = MultipleFileField(
        required=False,
        help_text="Upload Excel files using the exact registered filenames if you do not want to rely on a server-side directory.",
    )
    source_label = forms.CharField(
        required=False,
        initial="admin_import",
        help_text="Label stored on the resulting import batch.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        initial="Imported via Django admin",
    )
    reset = forms.BooleanField(
        required=False,
        help_text="Delete previously imported repository data before importing.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        specs = get_source_specs()
        self.fields["datasets"].choices = [
            (spec.dataset, f"{spec.dataset} ({spec.filename})") for spec in specs
        ]

    def clean(self):
        cleaned_data = super().clean()
        datasets = cleaned_data.get("datasets") or []
        uploads = cleaned_data.get("uploads") or []
        input_dir = (cleaned_data.get("input_dir") or "").strip()

        specs = resolve_source_specs(datasets=datasets)
        if not specs:
            raise forms.ValidationError("No registered source specifications matched the selected datasets.")

        selected_filenames = {spec.filename for spec in specs}
        upload_names = [Path(upload.name).name for upload in uploads]

        unknown_uploads = sorted(set(upload_names) - selected_filenames)
        if unknown_uploads:
            raise forms.ValidationError(
                f"Uploaded files are not registered in the source spec list: {', '.join(unknown_uploads)}"
            )

        if not input_dir and not uploads:
            raise forms.ValidationError("Provide either an input directory or one or more uploaded Excel files.")

        if uploads:
            missing_uploads = sorted(selected_filenames - set(upload_names))
            if missing_uploads and not input_dir:
                raise forms.ValidationError(
                    "When no input directory is provided, uploads must cover all selected registered files. "
                    f"Missing: {', '.join(missing_uploads)}"
                )

        cleaned_data["resolved_specs"] = specs
        return cleaned_data
