# Generated by Django 2.2.6 on 2020-01-21 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_user_organization"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="slug",
            field=models.SlugField(max_length=20, null=True, unique=True),
        ),
    ]
