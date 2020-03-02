# Generated by Django 3.0.2 on 2020-03-01 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aws_environments", "0016_auto_20200226_2206"),
    ]

    operations = [
        migrations.AddField(
            model_name="buildworker",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="buildworker",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
    ]
