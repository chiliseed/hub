# Generated by Django 3.0.2 on 2020-02-19 17:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("aws_environments", "0008_auto_20200216_2046"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="service", unique_together={("name", "project_id")},
        ),
        migrations.CreateModel(
            name="ServiceStatus",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("slug", models.SlugField(max_length=20, null=True, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("changes_pending", "Pending changes"),
                            ("ready", "Ready"),
                            ("error", "Failed to apply changes"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="statuses",
                        to="aws_environments.Service",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
    ]