import datetime

from django.core import exceptions, validators
from rest_framework import response, serializers, status

from aquacycl_project import constants, settings
from tj_packages import encrypt_decrypt, send_password_reset_mail
from users import models


def forgot_password(request: object):
    """
    To send a password reset link to the respective user's email

    Params:
        request: request object containing the user details
    """
    data = request.data
    user_email = data.get("email", "")
    if not user_email:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Email ID cannot be empty. Please provide a valid email address.",
                "validation_error_field": "email",
            },
            code="validation_error",
        )

    try:
        validators.validate_email(user_email)
    except exceptions.ValidationError:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Invalid email. Please check your input and try again.",
                "validation_error_field": "email",
            },
            code="validation_error",
        )

    user_profile = (
        models.UserProfileDetails.objects.filter(
            user__email=user_email,
            user__is_active=True,
        )
        .select_related("user")
        .first()
    )
    if user_profile:
        current_datetime = datetime.datetime.utcnow()
        data = (
            str(user_email)
            + "^^^"
            + current_datetime.strftime(constants.DATE_TIME_FORMAT)
        )
        token = encrypt_decrypt.encrypt(data=data)
        url = f"""{settings.FRONT_END_BASE_URL}resetpassword/?token={token}"""
        models.ResetTokenLog.objects.create(
            user=user_profile.user, token=token
        )
        username = (
            f"{user_profile.user.first_name} {user_profile.user.last_name}"
        )

        send_password_reset_mail.send_mail(user_email, username, url)
        res = {
            "result": True,
            "msg": "An email has been sent to your registered email address. Please follow the instructions in the email to reset your password.",  # noqa
        }
        return response.Response(res, status=status.HTTP_200_OK)
    else:
        msg = "Account not found. Please check your email and try again."
        return response.Response(
            {
                "result": False,
                "msg": msg,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
