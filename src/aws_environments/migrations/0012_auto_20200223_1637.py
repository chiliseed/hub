# Generated by Django 3.0.2 on 2020-02-23 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aws_environments", "0011_service_last_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(name="service", unique_together=set(),),
    ]