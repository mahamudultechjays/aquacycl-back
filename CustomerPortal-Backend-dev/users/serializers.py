from rest_framework import serializers

from aquacycl_project import constants
from users import models


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DesignationMaster
        fields = [
            "id",
            "name",
        ]


class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.ReadOnlyField(source="user.id")
    first_name = serializers.ReadOnlyField(source="user.first_name")
    last_name = serializers.ReadOnlyField(source="user.last_name")
    email = serializers.ReadOnlyField(source="user.email")
    user_type = serializers.ReadOnlyField(source="user_type.name")
    user_type_id = serializers.ReadOnlyField(source="user_type.id")

    class Meta:
        model = models.UserProfileDetails
        fields = [
            "user_id",
            "first_name",
            "last_name",
            "email",
            "user_type",
            "user_type_id",
        ]


class CompanySerializer(serializers.ModelSerializer):
    company_id = serializers.ReadOnlyField(source="id")
    company_name = serializers.ReadOnlyField(source="name")

    class Meta:
        model = models.Company
        fields = [
            "company_id",
            "company_name",
        ]


class SiteSerializer(serializers.ModelSerializer):
    site_id = serializers.ReadOnlyField(source="id")
    site_name = serializers.ReadOnlyField(source="name")
    company_id = serializers.ReadOnlyField(source="company.id")
    company_name = serializers.ReadOnlyField(source="company.name")

    class Meta:
        model = models.Site
        fields = [
            "company_id",
            "company_name",
            "site_id",
            "site_name",
        ]


class SiteMappingSerializer(serializers.ModelSerializer):
    site_id = serializers.ReadOnlyField(source="id")
    site_name = serializers.ReadOnlyField(source="name")

    class Meta:
        model = models.Site
        fields = [
            "site_id",
            "site_name",
        ]


class CompanySiteMappingSerializer(serializers.ModelSerializer):
    company_id = serializers.ReadOnlyField(source="id")
    company_name = serializers.ReadOnlyField(source="name")
    site_list = SiteMappingSerializer(
        source="site_set", many=True, read_only=True
    )

    class Meta:
        model = models.Company
        fields = [
            "company_id",
            "company_name",
            "site_list",
        ]


class UserSiteMappingSerializer(serializers.ModelSerializer):
    user_site_mapping_id = serializers.ReadOnlyField(
        source="usersitemapping.id"
    )
    company_id = serializers.ReadOnlyField(source="site.company.id")
    company_name = serializers.ReadOnlyField(source="site.company.name")
    site_name = serializers.ReadOnlyField(source="site.name")

    class Meta:
        model = models.UserSiteMapping
        fields = [
            "user_site_mapping_id",
            "company_id",
            "company_name",
            "site_id",
            "site_name",
        ]


class UserDetailSerializer(serializers.ModelSerializer):

    user_id = serializers.ReadOnlyField(source="id")
    country_code = serializers.ReadOnlyField(
        source="userprofiledetails.country_code"
    )
    mobile_number = serializers.ReadOnlyField(
        source="userprofiledetails.mobile_number"
    )
    designation_id = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    others_designation_name = serializers.ReadOnlyField(
        source="userprofiledetails.others_designation_name"
    )
    site_address = serializers.ReadOnlyField(
        source="userprofiledetails.site_address"
    )
    user_site_mapping_set = UserSiteMappingSerializer(
        source="usersitemapping_set", many=True, read_only=True
    )
    date_joined = serializers.SerializerMethodField()

    def get_designation_id(self, instance):
        designation = instance.userprofiledetails.designation
        if designation is not None:
            designation_id = designation.id
        else:
            designation_id = None
        return designation_id

    def get_designation_name(self, instance):
        designation = instance.userprofiledetails.designation
        if designation is not None:
            designation_name = designation.name
        else:
            designation_name = None
        return designation_name

    def get_date_joined(self, instance):
        date_joined = instance.userprofiledetails.date_joined
        if date_joined:
            date_joined = date_joined.strftime(constants.DATE_FORMAT)
        return date_joined

    class Meta:
        model = models.User
        fields = [
            "user_id",
            "first_name",
            "last_name",
            "email",
            "country_code",
            "mobile_number",
            "designation_id",
            "designation_name",
            "others_designation_name",
            "site_address",
            "date_joined",
            "user_site_mapping_set",
        ]


class UserProfileDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.ReadOnlyField(source="user.id")
    first_name = serializers.ReadOnlyField(source="user.first_name")
    last_name = serializers.ReadOnlyField(source="user.last_name")
    old_email = serializers.ReadOnlyField(source="user.email")
    designation_id = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    preference_site_id = serializers.ReadOnlyField(source="site_preference.id")
    preference_site_name = serializers.ReadOnlyField(
        source="site_preference.name"
    )
    preference_company_id = serializers.ReadOnlyField(
        source="site_preference.company.id"
    )
    preference_company_name = serializers.ReadOnlyField(
        source="site_preference.company.name"
    )

    def get_designation_id(self, instance):
        designation = instance.designation
        if designation is not None:
            designation_id = designation.id
        else:
            designation_id = None
        return designation_id

    def get_designation_name(self, instance):
        designation = instance.designation
        if designation is not None:
            designation_name = designation.name
        else:
            designation_name = None
        return designation_name

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        site_preference = instance.site_preference

        if not site_preference:
            representation["preference_site_id"] = None
            representation["preference_site_name"] = None
            representation["preference_company_id"] = None
            representation["preference_company_name"] = None

        return representation

    class Meta:
        model = models.UserProfileDetails
        fields = [
            "user_id",
            "first_name",
            "last_name",
            "old_email",
            "new_email",
            "is_email_verified",
            "country_code",
            "mobile_number",
            "designation_id",
            "designation_name",
            "others_designation_name",
            "preference_site_id",
            "preference_site_name",
            "preference_company_id",
            "preference_company_name",
            "profile_pic",
            "medium_profile_pic",
            "thumbnail_profile_pic",
        ]
