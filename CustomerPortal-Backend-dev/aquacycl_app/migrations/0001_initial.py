# Generated by Django 3.2 on 2023-07-28 10:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CronConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'cron_config',
            },
        ),
        migrations.CreateModel(
            name='SiteManifest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_repo_url', models.CharField(blank=True, max_length=2048, null=True)),
                ('owner', models.CharField(blank=True, max_length=2048, null=True)),
                ('repo', models.CharField(blank=True, max_length=2048, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('admin_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('site', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='users.site')),
            ],
            options={
                'db_table': 'site_manifest',
            },
        ),
        migrations.CreateModel(
            name='SiteManifestVersionHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('validated_date', models.DateField(blank=True, null=True)),
                ('file_version', models.CharField(blank=True, max_length=100, null=True)),
                ('manifest_file_name', models.CharField(blank=True, max_length=2048, null=True)),
                ('latest_commit_hash', models.CharField(blank=True, max_length=100, null=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('added_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('site_manifest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='version_history', to='aquacycl_app.sitemanifest')),
            ],
            options={
                'db_table': 'site_manifest_version_history',
            },
        ),
        migrations.CreateModel(
            name='SiteConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('config_name', models.CharField(blank=True, max_length=500, null=True)),
                ('latest_commit_hash', models.CharField(blank=True, max_length=100, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('site_manifest', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='aquacycl_app.sitemanifest')),
            ],
            options={
                'db_table': 'site_config',
            },
        ),
        migrations.CreateModel(
            name='ManifestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subtopic_bit_no', models.IntegerField(default=0, null=True)),
                ('subtopic_reported_on', models.CharField(blank=True, max_length=500, null=True)),
                ('file_version', models.CharField(blank=True, max_length=100, null=True)),
                ('manifest_file_name', models.CharField(blank=True, max_length=500, null=True)),
                ('data', models.JSONField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.site')),
            ],
            options={
                'db_table': 'manifest_log',
                'unique_together': {('subtopic_bit_no', 'subtopic_reported_on', 'site', 'file_version')},
            },
        ),
    ]
