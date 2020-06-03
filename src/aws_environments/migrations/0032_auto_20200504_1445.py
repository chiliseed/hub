# Generated by Django 3.0.5 on 2020-05-04 14:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("aws_environments", "0031_buildworker_project"),
    ]

    operations = [
        migrations.AddField(
            model_name="resource",
            name="service",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="resources",
                to="aws_environments.Service",
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="project",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="resources",
                to="aws_environments.Project",
            ),
        ),
    ]