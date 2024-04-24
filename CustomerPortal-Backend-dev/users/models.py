from django.conf import settings
from django.contrib import auth
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from tj_packages import s3_storage

User = auth.get_user_model()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """
    To generate User authentication token when receiving post_save signal upon creation of new user instance

    params:
        sender: The sender of the signal.
        instance: The user instance that was saved.
        created: A boolean indicating if the user was created or not.
        **kwargs: Additional keyword arguments passed to the function.

    Returns:
        None
    """
    if created:
        Token.objects.create(user=instance)


class DesignationMaster(models.Model):
    """
    Defines the possible designations for a user (eg: Engineer, Safety Officer)
    """

    name = models.CharField(max_length=64, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.name

    class Meta:
        db_table = "designation_master"


class UserType(models.Model):
    """
    Defines the types of users (eg: Admin, Staff, Customer)
    """

    name = models.CharField(max_length=64, blank=True, default="", unique=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.name

    class Meta:
        db_table = "user_type"


class Company(models.Model):
    """
    Used to store the details of companies under service
    """

    name = models.CharField(max_length=100, blank=True, null=True)
    manifest_config_name = models.CharField(
        max_length=100, blank=True, null=True
    )
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.name

    class Meta:
        db_table = "company"


class Site(models.Model):
    """
    Used to store information about location sites that are assoicated with companies
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)
    manifest_config_name = models.CharField(
        max_length=100, blank=True, null=True
    )
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return f"{self.company.name} - {self.name}"

    class Meta:
        db_table = "site"


class UserProfileDetails(models.Model):
    """
    Used to store user profile information.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.ForeignKey(UserType, on_delete=models.CASCADE)
    source = models.CharField(max_length=32, blank=True, default="")
    profile_pic = models.FileField(
        upload_to="profile/images",
        storage=s3_storage.PublicMediaStorage(),
        null=True,
        blank=True,
        default="",
    )
    medium_profile_pic = models.FileField(
        upload_to="profile/images/medium",
        storage=s3_storage.PublicMediaStorage(),
        null=True,
        blank=True,
        default="",
    )
    thumbnail_profile_pic = models.FileField(
        upload_to="profile/images/thumb",
        storage=s3_storage.PublicMediaStorage(),
        null=True,
        blank=True,
        default="",
    )
    country_code = models.CharField(max_length=24, blank=True, default="")
    mobile_number = models.CharField(max_length=16, blank=True, default="")
    is_email_verified = models.BooleanField(default=False)
    new_email = models.CharField(max_length=500, blank=True, default="")
    designation = models.ForeignKey(
        DesignationMaster,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="designation_user",
    )
    others_designation_name = models.CharField(
        max_length=100, blank=True, null=True, default=""
    )
    site_address = models.CharField(
        max_length=500, blank=True, null=True, default=""
    )
    site_preference = models.ForeignKey(
        Site, blank=True, null=True, on_delete=models.CASCADE
    )
    date_joined = models.DateField(blank=True, null=True)
    is_disabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.user.email

    class Meta:
        db_table = "user_profile_details"


class InviteUser(models.Model):
    """
    Used to store invite user information.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user"
    )
    invited_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="invited_user"
    )
    is_signed_up = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.user.first_name

    class Meta:
        db_table = "invite_user"
        unique_together = ["user", "invited_user"]


class AuditUserLogin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=12, blank=True, default="")
    login_time = models.CharField(max_length=256, blank=True, default="")
    logout_time = models.CharField(max_length=256, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.user.username

    class Meta:
        db_table = "user_login_audit"


class ResetTokenLog(models.Model):
    """
    Used to store password reset token information.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=500, blank=True, default="")
    is_expired = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.user.username

    class Meta:
        db_table = "reset_token_log"


class PasswordHistory(models.Model):
    """
    To store historical password hash data per user to avoid repetition
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    password = models.CharField(max_length=128)
    created_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.user.username

    class Meta:
        db_table = "password_history"


class UserSiteMapping(models.Model):
    """
    Used to store information regarding site-user association mappings
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return f"{self.user.first_name} - {self.site.name}"

    class Meta:
        db_table = "user_site_mapping"
        unique_together = ["user", "site"]
