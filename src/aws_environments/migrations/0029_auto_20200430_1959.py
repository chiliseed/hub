# Generated by Django 3.0.2 on 2020-04-30 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aws_environments", "0028_auto_20200430_1813"),
    ]

    operations = [
        migrations.AlterField(
            model_name="environment",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="environment",
            name="is_deleted",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="envstatus",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="envstatus",
            name="is_deleted",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="executionlog",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="executionlog",
            name="is_deleted",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="project",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="is_deleted",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="projectstatus",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="projectstatus",
            name="is_deleted",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="resource",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="resource",
            name="is_deleted",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="resourcestatus",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="resourcestatus",
            name="is_deleted",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="service",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="service",
            name="is_deleted",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="servicedeployment",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="servicedeployment",
            name="is_deleted",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="servicestatus",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="servicestatus",
            name="is_deleted",
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
