from rest_framework import serializers

from aquacycl_app import models
from aquacycl_project import constants


class ManifestHistorySerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    company_name = serializers.ReadOnlyField(
        source="site_manifest.site.company.name"
    )
    site_name = serializers.ReadOnlyField(source="site_manifest.site.name")
    manifest_name = serializers.SerializerMethodField()

    def get_date(self, instance):
        date = instance.validated_date
        if date:
            date = date.strftime(constants.DATE_FORMAT)
        return date

    def get_username(self, instance):
        user = instance.added_by
        if user:
            username = f"{user.first_name}"
        else:
            username = None
        return username

    def get_manifest_name(self, instance):
        manifest_file_name = instance.manifest_file_name
        if manifest_file_name:
            return manifest_file_name[:-4]
        else:
            return None

    class Meta:
        model = models.SiteManifestVersionHistory
        fields = [
            "id",
            "date",
            "username",
            "file_version",
            "company_name",
            "site_name",
            "manifest_name",
        ]


class FetchSnowflakeDataSerializer(serializers.Serializer):
    customer = serializers.CharField()
    site_name = serializers.CharField()
    plant = serializers.CharField()
