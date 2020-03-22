# Generated by Django 3.0.2 on 2020-03-22 18:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import fernet_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('aws_environments', '0021_service_default_dockerfile_path'),
    ]

    operations = [
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(max_length=20, null=True, unique=True)),
                ('identifier', models.CharField(max_length=150)),
                ('name', models.CharField(max_length=150)),
                ('kind', models.CharField(choices=[('database', 'Db'), ('cache', 'Cache')], max_length=50)),
                ('configuration', fernet_fields.fields.EncryptedTextField(default='{}')),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='aws_environments.Environment')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='executionlog',
            name='component',
            field=models.CharField(choices=[('service', 'Service'), ('project', 'Project'), ('environment', 'Environment'), ('build_worker', 'Build Worker'), ('deployment', 'Deployment'), ('resource', 'Resource')], db_index=True, max_length=50),
        ),
        migrations.CreateModel(
            name='ResourceStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(max_length=20, null=True, unique=True)),
                ('status', models.CharField(choices=[('changes_pending', 'Pending changes'), ('ready', 'Ready'), ('error', 'Failed to apply changes')], max_length=30)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statuses', to='aws_environments.Resource')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='resource',
            name='last_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resource_object', to='aws_environments.ResourceStatus'),
        ),
        migrations.AddField(
            model_name='resource',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aws_resources', to='organizations.Organization'),
        ),
    ]