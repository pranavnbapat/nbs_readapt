from __future__ import annotations

from django.db import models
from django.utils.text import slugify


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ImportBatch(TimestampedModel):
    source_label = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_imported = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.source_label} ({self.created_at:%Y-%m-%d %H:%M})"


class Country(TimestampedModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    country_code = models.CharField(max_length=8, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "countries"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Hazard(TimestampedModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class NbsType(TimestampedModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "NbS type"
        verbose_name_plural = "NbS types"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class RepositoryRecord(TimestampedModel):
    class SourceDataset(models.TextChoices):
        PAPERS = "papers", "Papers"
        NETWORK_PROJECTS = "network_projects", "Network Projects"
        EU_PROJECTS = "eu_projects", "EU Funded Projects"
        POLICIES = "policies", "Policies"

    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.SET_NULL,
        related_name="records",
        null=True,
        blank=True,
    )
    source_dataset = models.CharField(max_length=32, choices=SourceDataset.choices)
    source_sheet = models.CharField(max_length=255, blank=True)
    source_row_number = models.PositiveIntegerField()
    source_uid = models.CharField(max_length=255, unique=True)
    source_record_id = models.CharField(max_length=255)

    title = models.CharField(max_length=1024)
    source_database = models.TextField(blank=True)
    record_subtype = models.TextField(blank=True)
    document_type = models.TextField(blank=True)
    policy_level = models.TextField(blank=True)
    geographic_scope = models.TextField(blank=True)
    territorial_context = models.TextField(blank=True)
    environment_type = models.TextField(blank=True)
    implementation_stage = models.TextField(blank=True)
    community_engagement_level = models.TextField(blank=True)
    data_availability = models.TextField(blank=True)

    publication_year = models.IntegerField(null=True, blank=True)
    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)

    lead_organization = models.CharField(max_length=512, blank=True)
    authors = models.TextField(blank=True)
    affiliations = models.TextField(blank=True)
    acronym = models.TextField(blank=True)
    funding_source = models.TextField(blank=True)
    funding_contribution = models.TextField(blank=True)

    doi = models.CharField(max_length=512, blank=True)
    source_url = models.URLField(max_length=1000, blank=True)
    source_url_secondary = models.URLField(max_length=1000, blank=True)

    abstract = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    description = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    methods = models.TextField(blank=True)
    outcomes_targeted = models.TextField(blank=True)
    ecological_impacts = models.TextField(blank=True)
    socio_economic_impacts = models.TextField(blank=True)
    governance_insights = models.TextField(blank=True)
    finance_insights = models.TextField(blank=True)
    implementation_steps = models.TextField(blank=True)
    monitoring_reporting = models.TextField(blank=True)
    barriers = models.TextField(blank=True)
    enablers = models.TextField(blank=True)
    lessons = models.TextField(blank=True)
    key_findings = models.TextField(blank=True)
    enforcement_mechanisms = models.TextField(blank=True)
    nbs_relevance = models.TextField(blank=True)
    nbs_commitment = models.TextField(blank=True)

    country_display = models.TextField(blank=True)
    city_location = models.TextField(blank=True)
    location_text = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    keywords = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    normalized_payload = models.JSONField(default=dict, blank=True)

    countries = models.ManyToManyField(Country, related_name="records", blank=True)
    primary_hazards = models.ManyToManyField(Hazard, related_name="primary_records", blank=True)
    secondary_hazards = models.ManyToManyField(Hazard, related_name="secondary_records", blank=True)
    primary_nbs_types = models.ManyToManyField(NbsType, related_name="primary_records", blank=True)
    secondary_nbs_types = models.ManyToManyField(NbsType, related_name="secondary_records", blank=True)

    class Meta:
        ordering = ["source_dataset", "title"]

    def __str__(self) -> str:
        return f"{self.get_source_dataset_display()}: {self.title}"
