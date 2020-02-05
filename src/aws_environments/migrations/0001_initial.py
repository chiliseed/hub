# Generated by Django 3.0.2 on 2020-02-04 20:51

from django.db import migrations, models
import django.db.models.deletion
import fernet_fields.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(max_length=20, null=True, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('domain', models.CharField(default='', max_length=100)),
                ('region', models.CharField(choices=[('us-east-1', 'Nvirginia'), ('us-east-2', 'Ohio'), ('us-west-1', 'Ncalifornia'), ('us-west-2', 'Oregon')], default='us-east-1', max_length=20)),
                ('configuration', fernet_fields.fields.EncryptedTextField(default='{}')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aws_environments', to='organizations.Organization')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(max_length=20, null=True, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('configuration', fernet_fields.fields.EncryptedTextField(default='{}')),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='aws_environments.Environment')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aws_projects', to='organizations.Organization')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(max_length=20, null=True, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('subdomain', models.CharField(max_length=50)),
                ('configuration', fernet_fields.fields.EncryptedTextField(default='{}')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='services', to='aws_environments.Project')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExecutionLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(max_length=20, null=True, unique=True)),
                ('action', models.CharField(choices=[('create', 'Create'), ('destroy', 'Destroy'), ('update', 'Update'), ('outputs', 'Details')], max_length=50)),
                ('is_success', models.NullBooleanField()),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('params', fernet_fields.fields.EncryptedTextField(default='{}')),
                ('component', models.CharField(choices=[('service', 'Service'), ('project', 'Project'), ('environment', 'Environment')], max_length=50)),
                ('component_id', models.CharField(blank=True, max_length=100, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aws_runs', to='organizations.Organization')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]