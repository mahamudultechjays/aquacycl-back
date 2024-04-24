import datetime

from django.contrib import auth
from django.core import exceptions, validators
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from users import models

User = auth.get_user_model()


def sign_in(request: object, is_active=True):
    """
    To log in the user upon request

    Params:
        request: the request object containing the user details
        is_active: to check for user against active records

    Returns:
        user, token: a tuple containing the user object and associated token
    """
    ip_address = (
        request.META.get(
            "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")
        )
        .split(",")[0]
        .strip()
    )

    data = request.data
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Please enter both your email and password.",
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
                "msg": "Please enter a valid email address.",
                "validation_error_field": "email",
            },
            code="validation_error",
        )

    if not password:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Please enter both your email and password.",
                "validation_error_field": "password",
            },
            code="validation_error",
        )
    try:
        user_profile = models.UserProfileDetails.objects.select_related(
            "user", "user_type", "designation"
        ).get(
            user__email=email,
            user__is_active=is_active,
            date_joined__isnull=False,
        )
    except exceptions.ObjectDoesNotExist:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Invalid email or password. Please try again",
                "validation_error_field": "email",
            },
            code="validation_error",
        )

    if user_profile.is_disabled:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Your account is disabled and cannot access this application.",
                "validation_error_field": "email",
            },
            code="validation_error",
        )

    is_pass = user_profile.user.check_password(password)
    if not is_pass:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Invalid email or password. Please try again",
                "validation_error_field": "password",
            },
            code="validation_error",
        )

    update_user_login_details(
        user=user_profile.user,
        ip_address=ip_address,
    )
    user = user_profile.user
    token = get_token(user=user_profile.user)
    return user, token


def update_user_login_details(user: User, ip_address: str):
    current_time = datetime.datetime.now(tz=datetime.timezone.utc)
    user.last_login = current_time
    user.save()
    userLoginDetails = models.AuditUserLogin(
        user=user,
        login_time=current_time,
    )
    userLoginDetails.save()


def get_token(user: User):
    token = Token.objects.get_or_create(user=user)[0]
    return token
