# Generated by Django 2.2.6 on 2019-10-07 21:33
# noqa

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("users", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="slug",
            field=models.SlugField(max_length=20, null=True),
        )
    ]
