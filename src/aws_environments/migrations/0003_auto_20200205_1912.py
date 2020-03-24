# Generated by Django 3.0.2 on 2020-02-05 19:12

import aws_environments.models
from django.db import migrations, models

import aws_environments.models.validators


class Migration(migrations.Migration):

    dependencies = [
        ("aws_environments", "0002_auto_20200205_1653"),
    ]

    operations = [
        migrations.AlterField(
            model_name="environment",
            name="domain",
            field=models.CharField(
                max_length=200,
                validators=[
                    aws_environments.models.validators.OptionalSchemeURLValidator()
                ],
            ),
        ),
    ]
