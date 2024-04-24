from django.contrib import auth
from rest_framework import serializers

User = auth.get_user_model()


class Token:
    def __get__(self, obj):
        return self.value

    def __set__(self, obj, value):
        if not value:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Token missing or empty.",
                    "validation_error_field": "token",
                },
                code="validation_error",
            )
        self.value = value


class Password:
    def __get__(self, obj):
        return self.value

    def __set__(self, obj, value):
        if not value:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Password cannot be empty, Please provide a valid password.",
                    "validation_error_field": "password",
                },
                code="validation_error",
            )
        if type(value) is not str:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Password should be a string",
                    "validation_error_field": "password",
                },
                code="",
            )
        if len(value) < 6 or len(value) > 8:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Password should have a minimum length of 6 characters, maximum length of 8 characters and should contain at least one upper case letter, one lower case letter and one digit.",
                    "validation_error_field": "password",
                },
                code="validation_error",
            )
        self.value = value


class NewPassword:
    def __get__(self, obj):
        return self.value

    def __set__(self, obj, value):
        if not value:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "New password cannot be empty, Please provide a valid password.",
                    "validation_error_field": "new_password",
                },
                code="validation_error",
            )

        if type(value) is not str:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "New password should be a string.",
                    "validation_error_field": "new_password",
                },
                code="validation_error",
            )

        if len(value) < 6 or len(value) > 8:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "New password should have a minimum length of 6 characters, maximum length of 8 characters and should contain at least one upper case letter, one lower case letter and one digit.",
                    "validation_error_field": "new_password",
                },
                code="validation_error",
            )
        self.value = value


class CurrentPassword:
    def __get__(self, obj):
        return self.value

    def __set__(self, obj, value):
        if not value:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Current password cannot be empty, Please provide a valid password.",
                    "validation_error_field": "current_password",
                },
                code="validation_error",
            )
        if type(value) is not str:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Current password should be a string.",
                    "validation_error_field": "current_password",
                }
            )
        self.value = value


class ConfirmPassword:
    def __get__(self, obj):
        return self.value

    def __set__(self, obj, value):
        if not value:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Confirm password cannot be empty, Please provide a valid password.",
                    "validation_error_field": "confirm_password",
                },
                code="validation_error",
            )
        if type(value) is not str:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Confirm password should be a string.",
                    "validation_error_field": "confirm_password",
                }
            )
        if len(value) < 6 or len(value) > 8:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Confirm password should have a minimum length of 6 characters, maximum length of 8 characters and should contain at least one upper case letter, one lower case letter and one digit.",
                    "validation_error_field": "confirm_password",
                },
                code="validation_error",
            )
        self.value = value


class ResetPassword:
    token = Token()
    password = Password()
    confirm_password = ConfirmPassword()

    def __init__(self, token, password, confirm_password):
        self.token = token
        self.password = password
        self.confirm_password = confirm_password


class ChangePassword:
    current_password = CurrentPassword()
    new_password = NewPassword()
    confirm_password = ConfirmPassword()

    def __init__(self, current_password, new_password, confirm_password):
        self.current_password = current_password
        self.new_password = new_password
        self.confirm_password = confirm_password
