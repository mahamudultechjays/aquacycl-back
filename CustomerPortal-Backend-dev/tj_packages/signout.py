import datetime

from django.core import exceptions
from rest_framework import response, serializers, status
from rest_framework.authtoken.models import Token

from users import models


def logout(request):
    """
    To log out a user upon request

    Params:
        request: the request object containing user details

    Returns:
        Response: A JSON response indicating the result of the logout operation.

    """
    user = request.user
    user_login_details = models.AuditUserLogin.objects.filter(
        user=user.id, is_active=True
    ).last()
    if not user_login_details:
        return response.Response(
            {"result": False, "msg": "Invalid User"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user_login_details.logout_time = datetime.datetime.now()
    user_login_details.save()
    return response.Response(
        {"result": True, "msg": "Logged out successfully"},
        status=status.HTTP_200_OK,
    )


def delete_token(user_id: int):
    """
    To delete user token

    Params:
        user_id: the pk of user record
    """
    try:
        token = Token.objects.get(user=user_id)
    except exceptions.ObjectDoesNotExist:
        raise serializers.ValidationError(
            {"result": False, "msg": "User Already Deactivated"},
            code="validation_error",
        )
    token.delete()
