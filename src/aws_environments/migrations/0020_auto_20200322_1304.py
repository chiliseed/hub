# Generated by Django 3.0.2 on 2020-03-22 13:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aws_environments", "0019_environmentvariable"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="has_web_interface",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="service",
            name="alb_port_http",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="service",
            name="alb_port_https",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="service",
            name="container_port",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="service",
            name="subdomain",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
