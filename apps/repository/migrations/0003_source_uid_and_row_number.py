from django.db import migrations, models


def populate_source_identity(apps, schema_editor):
    RepositoryRecord = apps.get_model("repository", "RepositoryRecord")
    for record in RepositoryRecord.objects.all().iterator():
        record.source_row_number = record.id
        record.source_uid = f"legacy:{record.id}"
        record.save(update_fields=["source_row_number", "source_uid"])


class Migration(migrations.Migration):

    dependencies = [
        ("repository", "0002_widen_record_metadata_fields"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="repositoryrecord",
            name="uniq_repository_record_source_id",
        ),
        migrations.AddField(
            model_name="repositoryrecord",
            name="source_row_number",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="repositoryrecord",
            name="source_uid",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.RunPython(populate_source_identity, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="source_row_number",
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="source_uid",
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
