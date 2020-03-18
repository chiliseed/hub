# Generated by Django 3.0.2 on 2020-03-18 18:28

from django.db import migrations, models
import django.db.models.deletion
import fernet_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0001_initial"),
        ("aws_environments", "0018_auto_20200302_2128"),
    ]

    operations = [
        migrations.CreateModel(
            name="EnvironmentVariable",
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
                ("key_name", models.CharField(max_length=140)),
                (
                    "key_value",
                    fernet_fields.fields.EncryptedCharField(default="", max_length=250),
                ),
                ("is_secret", models.BooleanField(default=True)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="env_vars",
                        to="organizations.Organization",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="env_vars",
                        to="aws_environments.Service",
                    ),
                ),
            ],
            options={"unique_together": {("service_id", "key_name")},},
        ),
    ]
