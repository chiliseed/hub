# Generated by Django 3.0.2 on 2020-03-24 19:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aws_environments', '0024_auto_20200322_2057'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='deleted_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='resource',
            name='engine',
            field=models.CharField(choices=[('postgres', 'Postgres'), ('redis', 'Redis')], default='redis', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resource',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='resource',
            name='preset',
            field=models.CharField(choices=[('dev', 'Dev'), ('prod', 'Prod')], default='dev', max_length=50),
            preserve_default=False,
        ),
    ]
