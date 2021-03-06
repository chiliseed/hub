# Generated by Django 3.0.2 on 2020-02-11 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aws_environments", "0004_auto_20200209_1835"),
    ]

    operations = [
        migrations.AlterField(
            model_name="executionlog",
            name="component",
            field=models.CharField(
                choices=[
                    ("service", "Service"),
                    ("project", "Project"),
                    ("environment", "Environment"),
                ],
                db_index=True,
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="executionlog",
            name="component_id",
            field=models.CharField(
                blank=True, db_index=True, max_length=100, null=True
            ),
        ),
    ]
