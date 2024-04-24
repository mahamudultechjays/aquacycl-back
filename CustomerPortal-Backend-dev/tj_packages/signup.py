import re
from typing import Tuple

from django.contrib import auth
from django.core import exceptions, validators
from django.db import models as django_models
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from aquacycl_project import constants
from tj_packages import user_profile
from users import models

User = auth.get_user_model()


def create_user(
    request: object,
    token_email: str,
    token_user_type_id: int,
    is_active=True,
) -> Tuple[django_models.Model, str]:
    """
    Create User profile based on the provided request data after validations.

    Params:
        request: request object containing the user details
        is_active: To specify whether the user is active

    Returns:
        user, token: a tuple containing the created user object and associated token
    """
    data = request.data
    user_type_id = data.get("user_type_id", "")
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    email = data.get("email", "").strip().lower()
    country_code = data.get("country_code", "").strip()
    mobile_number = data.get("mobile_number", "").strip()
    designation_id = data.get("designation_id", None)
    others_designation_name = data.get("others_designation_name", "").strip()
    site_address = data.get("site_address", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    source = data.get("source", "")

    if not user_type_id:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "User Type missing or empty.",
                "validation_error_field": "user_type_id",
            },
            code="validation_error",
        )

    if user_type_id != token_user_type_id:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Invalid user type id",
                "validation_error_field": "user_type",
            },
            code="validation_error",
        )

    try:
        user_type_object = models.UserType.objects.get(
            id=user_type_id, is_active=True
        )
    except exceptions.ObjectDoesNotExist:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Invalid User Type.",
                "validation_error_field": "user_type_id",
            },
            code="validation_error",
        )

    if not email:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Email ID cannot be empty. Please provide a valid email address.",
                "validation_error_field": "email",
            },
            code="validation_error",
        )

    try:
        validators.validate_email(email)
    except exceptions.ValidationError:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Invalid Email ID format.",
                "validation_error_field": "email",
            },
            code="validation_error",
        )

    if email != token_email:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Email address does not match with the email given to Admin.",
                "validation_error_field": "email",
            },
            code="validation_error",
        )

    if models.UserProfileDetails.objects.filter(
        user__email=token_email,
        user__is_active=True,
        date_joined__isnull=False,
    ).exists():
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Email ID already exists in system!",
                "validation_error_field": "email",
            },
            code="validation_error",
        )

    if not first_name:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "First name cannot be empty. Please provide a valid first name.",
                "validation_error_field": "first_name",
            },
            code="validation_error",
        )

    if len(first_name) < 2:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Please enter a valid first name with more than one character.",
                "validation_error_field": "first_name",
            },
            code="validation_error",
        )

    if len(first_name) > 50:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "First Name exceeds the maximum length of 50 characters.",
                "validation_error_field": "first_name",
            },
            code="validation_error",
        )

    if not first_name.isalpha():
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "First Name should only contain alphabetic characters.",
                "validation_error_field": "first_name",
            },
            code="validation_error",
        )

    if not last_name:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Last name cannot be empty. Please provide a valid last name.",
                "validation_error_field": "last_name",
            },
            code="validation_error",
        )

    if len(last_name) < 2:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Please enter a valid last name with more than one character.",
                "validation_error_field": "last_name",
            },
            code="validation_error",
        )

    if len(last_name) > 50:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Last Name exceeds the maximum length of 50 characters.",
                "validation_error_field": "last_name",
            },
            code="validation_error",
        )

    if not last_name.isalpha():
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Last Name should only contain alphabetic characters.",
                "validation_error_field": "last_name",
            },
            code="validation_error",
        )

    if mobile_number:
        if not country_code:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Country code missing or empty.",
                    "validation_error_field": "country_code",
                },
                code="validation_error",
            )

        if not re.match(r"^[0-9]{10}$", mobile_number):
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Please enter a valid mobile number.",
                    "validation_error_field": "mobile_nubmer",
                },
                code="validation_error",
            )

    if designation_id:
        try:
            designation_object = models.DesignationMaster.objects.get(
                id=designation_id, is_active=True
            )
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid Designation.",
                    "validation_error_field": "desingation",
                },
                code="validation_error",
            )

        if designation_object.id == constants.DesignationNames.OTHERS:
            if not others_designation_name:
                raise serializers.ValidationError(
                    {
                        "result": False,
                        "msg": "Designation cannot be empty. Please provide a valid designation.",
                        "validation_error_field": "others_designation_name",
                    },
                    code="validation_error",
                )

            if len(others_designation_name) < 2:
                raise serializers.ValidationError(
                    {
                        "result": False,
                        "msg": " Please enter a valid designation with more than one character.",
                        "validation_error_field": "others_designation_name",
                    },
                    code="validation_error",
                )

            if len(others_designation_name) > 60:
                raise serializers.ValidationError(
                    {
                        "result": False,
                        "msg": "Designation exceeds the maximum length of 60 characters.",
                        "validation_error_field": "others_designation_name",
                    },
                    code="validation_error",
                )

            if not others_designation_name.replace(" ", "").isalpha():
                raise serializers.ValidationError(
                    {
                        "result": False,
                        "msg": "Please enter a valid designation without numeric or special characters.",
                        "validation_error_field": "others_designation_name",
                    },
                    code="validation_error",
                )
        else:
            others_designation_name = ""
    else:
        designation_object = None
        others_designation_name = ""

    if site_address and len(site_address) > 200:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Site Address exceeds the maximum length of 200 characters.",
                "validation_error_field": "site_address",
            },
            code="validation_error",
        )

    if not password:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Password cannot be empty, Please provide a valid password.",
                "validation_error_field": "password",
            },
            code="validation_error",
        )

    if not confirm_password:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Confirm Password cannot be empty, Please provide a valid password.",
                "validation_error_field": "confirm_password",
            },
            code="validation_error",
        )

    if (
        len(password) < 6
        or len(confirm_password) < 6
        or len(password) > 8
        or len(confirm_password) > 8
    ):
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Password should have a minimum length of 6 characters, maximum length of 8 characters and should contain at least one upper case letter, one lower case letter and one digit.",
                "validation_error_field": "password",
            },
            code="validation_error",
        )

    if password != confirm_password:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Confirm Password does not match the password.",
                "validation_error_field": "confirm_password",
            },
            code="validation_error",
        )

    if not source:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Source missing or empty.",
                "validation_error_field": "source",
            },
            code="validation_error",
        )

    if (
        user_type_object.id == constants.UserTypeNames.STAFF
        or user_type_object.id == constants.UserTypeNames.ADMIN
    ):
        site_address = ""

    user_profile_data = (
        models.UserProfileDetails.objects.select_related("user")
        .filter(
            user__email=token_email,
            date_joined__isnull=True,
        )
        .first()
    )

    if user_profile_data:
        user_profile_details = user_profile.update_user_and_profile_data(
            user_profile_data=user_profile_data,
            first_name=first_name,
            last_name=last_name,
            password=password,
            country_code=country_code,
            mobile_number=mobile_number,
            user_type_object=user_type_object,
            designation_object=designation_object,
            others_designation_name=others_designation_name,
            site_address=site_address,
            source=source,
            is_active=is_active,
        )
        user = user_profile_details.user
        invited_user_record = models.InviteUser.objects.get(
            invited_user=user, is_active=True
        )
        invited_user_record.is_signed_up = True
        invited_user_record.save()
        models.PasswordHistory.objects.create(
            user=user, password=user.password
        )

    else:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Invalid Token for sign up process.",
            },
            code="validation_error",
        )

    token = get_token(user=user)
    return user, token


def get_token(user: User):
    """
    Retrive or generate authentication token for the given user

    Params:
        user: user model object

    Returns:
        token: token associated with the given user
    """
    token = Token.objects.get_or_create(user=user)[0]
    return token
