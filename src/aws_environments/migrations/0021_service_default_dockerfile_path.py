# Generated by Django 3.0.2 on 2020-03-22 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aws_environments', '0020_auto_20200322_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='default_dockerfile_path',
            field=models.CharField(default='./Dockerfile', max_length=100),
        ),
    ]
