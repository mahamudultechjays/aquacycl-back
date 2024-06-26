# Generated by Django 3.2 on 2023-07-28 10:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import tj_packages.s3_storage


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('manifest_config_name', models.CharField(blank=True, max_length=100, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'company',
            },
        ),
        migrations.CreateModel(
            name='DesignationMaster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default='', max_length=64)),
                ('is_active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'designation_master',
            },
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('manifest_config_name', models.CharField(blank=True, max_length=100, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.company')),
            ],
            options={
                'db_table': 'site',
            },
        ),
        migrations.CreateModel(
            name='UserType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default='', max_length=64, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'user_type',
            },
        ),
        migrations.CreateModel(
            name='UserProfileDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(blank=True, default='', max_length=32)),
                ('profile_pic', models.FileField(blank=True, default='', null=True, storage=tj_packages.s3_storage.PublicMediaStorage(), upload_to='profile/images')),
                ('medium_profile_pic', models.FileField(blank=True, default='', null=True, storage=tj_packages.s3_storage.PublicMediaStorage(), upload_to='profile/images/medium')),
                ('thumbnail_profile_pic', models.FileField(blank=True, default='', null=True, storage=tj_packages.s3_storage.PublicMediaStorage(), upload_to='profile/images/thumb')),
                ('country_code', models.CharField(blank=True, default='', max_length=24)),
                ('mobile_number', models.CharField(blank=True, default='', max_length=16)),
                ('is_email_verified', models.BooleanField(default=False)),
                ('new_email', models.CharField(blank=True, default='', max_length=500)),
                ('others_designation_name', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('site_address', models.CharField(blank=True, default='', max_length=500, null=True)),
                ('date_joined', models.DateField(blank=True, null=True)),
                ('is_disabled', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('designation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='designation_user', to='users.designationmaster')),
                ('site_preference', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.site')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('user_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.usertype')),
            ],
            options={
                'db_table': 'user_profile_details',
            },
        ),
        migrations.CreateModel(
            name='ResetTokenLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(blank=True, default='', max_length=500)),
                ('is_expired', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'reset_token_log',
            },
        ),
        migrations.CreateModel(
            name='PasswordHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'password_history',
            },
        ),
        migrations.CreateModel(
            name='AuditUserLogin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(blank=True, default='', max_length=12)),
                ('login_time', models.CharField(blank=True, default='', max_length=256)),
                ('logout_time', models.CharField(blank=True, default='', max_length=256)),
                ('is_active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_login_audit',
            },
        ),
        migrations.CreateModel(
            name='UserSiteMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.site')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_site_mapping',
                'unique_together': {('user', 'site')},
            },
        ),
        migrations.CreateModel(
            name='InviteUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_signed_up', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('invited_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invited_user', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'invite_user',
                'unique_together': {('user', 'invited_user')},
            },
        ),
    ]
