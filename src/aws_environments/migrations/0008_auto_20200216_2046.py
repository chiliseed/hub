# Generated by Django 3.0.2 on 2020-02-16 20:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0001_initial"),
        ("aws_environments", "0007_auto_20200216_1659"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="environment", unique_together={("organization_id", "name")},
        ),
    ]
