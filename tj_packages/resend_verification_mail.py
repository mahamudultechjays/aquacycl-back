from django.contrib import auth
from django.core import exceptions
from rest_framework import serializers

from tj_packages import send_verification_mail
from users import models

User = auth.get_user_model()


def send(email: str):
    if not email:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Email should not be empty.",
                "validation_error_field": "email",
            },
            code="validation_error",
        )
    try:
        user_details = models.UserProfileDetails.objects.select_related(
            "user"
        ).get(user__email=email)
    except exceptions.ObjectDoesNotExist:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Email not Exist to resend verification mail.",
                "validation_error_field": "email",
            },
            code="validation_error",
        )
    if user_details.is_email_verified:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Email Already Verified, Please do Sign in.",
                "validation_error_field": "email",
            },
            code="validation_error",
        )
    user = user_details.user
    user_type = user_details.user_type

    send_verification_mail.send_mail(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        user_type=user_type,
    )
    return user
