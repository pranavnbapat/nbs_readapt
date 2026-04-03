from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("repository", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="repositoryrecord",
            name="source_database",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="record_subtype",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="document_type",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="policy_level",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="geographic_scope",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="territorial_context",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="environment_type",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="implementation_stage",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="community_engagement_level",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="data_availability",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="acronym",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="funding_source",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="repositoryrecord",
            name="funding_contribution",
            field=models.TextField(blank=True),
        ),
    ]
