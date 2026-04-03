from __future__ import annotations

from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from .forms import RepositoryImportForm
from .models import Country, Hazard, ImportBatch, NbsType, RepositoryRecord
from .services import InitialInputImporter
from .source_specs import get_source_specs
from .validation import RepositorySourceValidator


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "source_label", "records_imported", "started_at", "completed_at")
    search_fields = ("source_label",)
    change_list_template = "admin/repository/importbatch/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-sources/",
                self.admin_site.admin_view(self.import_sources_view),
                name="repository_importbatch_import_sources",
            ),
        ]
        return custom_urls + urls

    def import_sources_view(self, request: HttpRequest):
        form = RepositoryImportForm(request.POST or None, request.FILES or None)
        validation_results = None

        if request.method == "POST" and form.is_valid():
            try:
                resolved_specs = form.cleaned_data["resolved_specs"]
                input_path = self._materialize_input_dir(form)
                validator = RepositorySourceValidator(input_dir=input_path)
                validation_results = validator.validate_specs(resolved_specs)

                if request.POST.get("action") == "validate":
                    if any(result.status == "error" for result in validation_results):
                        self.message_user(request, "Validation found blocking errors.", level=messages.ERROR)
                    elif any(result.status == "warning" for result in validation_results):
                        self.message_user(request, "Validation completed with warnings.", level=messages.WARNING)
                    else:
                        self.message_user(request, "Validation passed.", level=messages.SUCCESS)
                else:
                    if any(result.status == "error" for result in validation_results):
                        self.message_user(
                            request,
                            "Import blocked because validation found errors. Review the report below.",
                            level=messages.ERROR,
                        )
                    else:
                        importer = InitialInputImporter(input_dir=input_path)
                        batch = importer.import_all(
                            reset=form.cleaned_data.get("reset", False),
                            specs=resolved_specs,
                            source_label=form.cleaned_data.get("source_label") or "admin_import",
                            notes=form.cleaned_data.get("notes") or "Imported via Django admin",
                        )
                        self.message_user(
                            request,
                            f"Imported {batch.records_imported} records into batch {batch.id}.",
                            level=messages.SUCCESS,
                        )
                        return HttpResponseRedirect(reverse("admin:repository_importbatch_changelist"))
            except Exception as exc:
                self.message_user(request, f"Import/validation failed: {exc}", level=messages.ERROR)

        context = {
            **self.admin_site.each_context(request),
            "title": "Import Repository Sources",
            "opts": self.model._meta,
            "form": form,
            "registered_sources": get_source_specs(),
            "validation_results": validation_results,
        }
        return TemplateResponse(request, "admin/repository/import_sources.html", context)

    def _materialize_input_dir(self, form: RepositoryImportForm) -> Path:
        input_dir = (form.cleaned_data.get("input_dir") or "").strip()
        uploads = form.cleaned_data.get("uploads") or []
        if uploads:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            upload_dir = settings.MEDIA_ROOT / "import_uploads" / timestamp
            upload_dir.mkdir(parents=True, exist_ok=True)
            for upload in uploads:
                target = upload_dir / Path(upload.name).name
                with target.open("wb+") as destination:
                    for chunk in upload.chunks():
                        destination.write(chunk)
            return upload_dir
        return Path(input_dir)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "country_code", "updated_at")
    search_fields = ("name", "country_code")


@admin.register(Hazard)
class HazardAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at")
    search_fields = ("name",)


@admin.register(NbsType)
class NbsTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at")
    search_fields = ("name",)


@admin.register(RepositoryRecord)
class RepositoryRecordAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source_dataset",
        "source_uid",
        "source_record_id",
        "publication_year",
        "implementation_stage",
    )
    list_filter = ("source_dataset", "implementation_stage", "policy_level")
    search_fields = ("title", "source_uid", "source_record_id", "doi", "lead_organization")
