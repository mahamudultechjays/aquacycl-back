from django.contrib import auth
from django.db import models

from users import models as user_models

User = auth.get_user_model()


class SiteManifest(models.Model):
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.OneToOneField(user_models.Site, on_delete=models.CASCADE)
    site_repo_url = models.CharField(max_length=2048, blank=True, null=True)
    owner = models.CharField(max_length=2048, blank=True, null=True)
    repo = models.CharField(max_length=2048, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return f"{self.admin_user.first_name} {self.site.name}"

    class Meta:
        db_table = "site_manifest"


class SiteManifestVersionHistory(models.Model):
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    site_manifest = models.ForeignKey(
        SiteManifest, on_delete=models.CASCADE, related_name="version_history"
    )
    validated_date = models.DateField(blank=True, null=True)
    file_version = models.CharField(max_length=100, blank=True, null=True)
    manifest_file_name = models.CharField(
        max_length=2048, blank=True, null=True
    )
    latest_commit_hash = models.CharField(
        max_length=100, blank=True, null=True
    )
    is_primary = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return f"{self.manifest_file_name}"

    class Meta:
        db_table = "site_manifest_version_history"


class ManifestLog(models.Model):
    subtopic_bit_no = models.IntegerField(null=True, default=0)
    subtopic_reported_on = models.CharField(
        max_length=500, blank=True, null=True
    )
    site = models.ForeignKey(user_models.Site, on_delete=models.CASCADE)
    file_version = models.CharField(max_length=100, blank=True, null=True)
    manifest_file_name = models.CharField(
        max_length=500, blank=True, null=True
    )
    data = models.JSONField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return f"{self.subtopic_bit_no} {self.subtopic_reported_on}"

    class Meta:
        db_table = "manifest_log"
        unique_together = (
            "subtopic_bit_no",
            "subtopic_reported_on",
            "site",
            "file_version",
        )


class SiteConfig(models.Model):
    site_manifest = models.OneToOneField(
        SiteManifest,
        on_delete=models.CASCADE,
    )
    config_name = models.CharField(max_length=500, blank=True, null=True)
    latest_commit_hash = models.CharField(
        max_length=100, blank=True, null=True
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return f"{self.site_manifest.site_repo_url} {self.config_name}"

    class Meta:
        db_table = "site_config"


class CronConfig(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return f"{self.name} {self.updated_on}"

    class Meta:
        db_table = "cron_config"
