# Generated by Django 3.0.2 on 2020-04-30 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20200423_1352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_deleted',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
