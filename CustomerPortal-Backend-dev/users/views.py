import ast
import csv
import datetime
import re

from django.contrib import auth
from django.core import exceptions
from django.http import HttpResponse
from rest_framework import parsers, permissions, response, status, views

from aquacycl_project import constants
from tj_packages import (
    encrypt_decrypt,
    forgot_password,
    send_verification_mail,
    signin,
    signout,
    signup,
    user_profile,
)
from users import controllers, models
from users import serializers as user_serializers
from users import validator

User = auth.get_user_model()


class Signup(views.APIView):
    """
    API endpoint to handle user signup requests
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        signup_invite_token = request.data.get("invite_token", "")
        user_controller = controllers.UserController()
        if not signup_invite_token:
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid URL - Token Missing or Empty",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        result, data = encrypt_decrypt.decrypt(signup_invite_token)
        if result:
            token_user_type_id, token_email, token_datetime_str = str(
                data
            ).split("^^^")
            token_log = user_controller.check_signup_invite_token(
                token=signup_invite_token,
                token_datetime_str=token_datetime_str,
            )

            is_email_active = user_controller.check_if_email_already_active(
                email=token_email
            )

            if is_email_active:
                token_log.is_expired = True
                token_log.token = ""
                token_log.save()
                return response.Response(
                    {
                        "result": False,
                        "msg": "Expired sign up link.",
                        "validation_error_field": "token",
                        "validation_error_message": "Expired token",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user, token = signup.create_user(
                request=request,
                token_email=token_email,
                token_user_type_id=int(token_user_type_id),
            )

            token_log.is_expired = True
            token_log.token = ""
            token_log.save()

            data = {
                "user_id": user.id,
                "user_type_id": user.userprofiledetails.user_type.id,
                "user_type": user.userprofiledetails.user_type.name,
                "token": token.key,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "country_code": user.userprofiledetails.country_code,
                "mobile_number": user.userprofiledetails.mobile_number,
                "designation_id": user.userprofiledetails.designation_id,
                "others_designation_name": user.userprofiledetails.others_designation_name,
                "site_address": user.userprofiledetails.site_address,
                "date_joined": user.userprofiledetails.date_joined,
            }
            result = {
                "result": True,
                "msg": "Registered Successfully",
                "data": data,
            }
            return response.Response(result, status=status.HTTP_200_OK)

        return response.Response(
            {
                "result": False,
                "msg": "Invalid Token for sign up process",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request):
        query_params = request.query_params
        signup_invite_token = query_params.get("invite_token", "")
        if not signup_invite_token:
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid URL - Token Missing or Empty",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        result, data = encrypt_decrypt.decrypt(signup_invite_token)
        user_controller = controllers.UserController()
        if result:
            token_user_type_id, token_email, token_datetime_str = str(
                data
            ).split("^^^")

            token_log = user_controller.check_signup_invite_token(
                token=signup_invite_token,
                token_datetime_str=token_datetime_str,
            )

            user_profile_details = user_controller.get_user_by_email_user_type(
                email=token_email,
                user_type_id=int(token_user_type_id),
            )
            invited_user_record = user_controller.get_invited_user(
                invited_user=user_profile_details.user
            )
            if invited_user_record.is_signed_up:
                token_log.is_expired = True
                token_log.token = ""
                token_log.save()
                return response.Response(
                    {
                        "result": False,
                        "msg": "Expired sign up link.",
                        "validation_error_field": "token",
                        "validation_error_message": "Expired token",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data = {
                "user_id": user_profile_details.user.id,
                "user_type_id": user_profile_details.user_type.id,
                "user_type": user_profile_details.user_type.name,
                "email": user_profile_details.user.email,
                "first_name": user_profile_details.user.first_name,
                "last_name": user_profile_details.user.last_name,
            }
            return response.Response(
                {
                    "result": True,
                    "msg": "Token is valid for sign up",
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )
        return response.Response(
            {
                "result": False,
                "msg": "Invalid Token for sign up process",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class Designations(views.APIView):
    """
    API endpoint to provide the list of designations
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user_controller = controllers.UserController()
        designation_objects = user_controller.get_designations()
        serialized_data = user_serializers.DesignationSerializer(
            designation_objects, many=True
        ).data
        return response.Response(
            {
                "result": True,
                "msg": "Success",
                "data": serialized_data,
            },
            status=status.HTTP_200_OK,
        )


class Company(views.APIView):
    """
    API endpoint to provide list of companies
    """

    def get(self, request):
        user = request.user
        query_params = request.query_params
        is_company_site_mapping_list = query_params.get(
            "is_company_site_mapping_list", False
        )
        by_user = query_params.get("by_user", None)

        user_controller = controllers.UserController()

        if is_company_site_mapping_list:
            company_objects = user_controller.get_companies_with_sites()
            serialized_data = user_serializers.CompanySiteMappingSerializer(
                company_objects, many=True
            ).data
        else:
            company_objects = user_controller.get_companies()
            if by_user is not None and ast.literal_eval(by_user):
                user_profile = user_controller.get_user_profile_by_user(
                    user=user
                )
                if user_profile.user_type.id in [
                    constants.UserTypeNames.CUSTOMER,
                    constants.UserTypeNames.STAFF,
                ]:
                    company_objects = user_controller.get_companies_by_user(
                        user=user
                    )
            serialized_data = user_serializers.CompanySerializer(
                company_objects, many=True
            ).data
        return response.Response(
            {
                "result": True,
                "msg": "Success",
                "data": serialized_data,
            },
            status=status.HTTP_200_OK,
        )


class Site(views.APIView):
    """
    API endpoint to provide list of sites
    """

    def get(self, request):
        user = request.user
        query_params = request.query_params
        company_ids = query_params.get("company_ids", "")
        by_user = query_params.get("by_user", None)
        user_controller = controllers.UserController()
        company_ids = ast.literal_eval(company_ids)

        site_objects = user_controller.get_sites()
        user_profile = user_controller.get_user_profile_by_user(user=user)
        if company_ids:
            site_objects = user_controller.get_sites_by_company_ids(
                company_ids=company_ids
            )

        if by_user is not None and ast.literal_eval(by_user):
            if user_profile.user_type.id in [
                constants.UserTypeNames.CUSTOMER,
                constants.UserTypeNames.STAFF,
            ]:
                site_objects = user_controller.get_sites_by_user(user=user)

        if by_user is not None and ast.literal_eval(by_user) and company_ids:
            if user_profile.user_type.id in [
                constants.UserTypeNames.CUSTOMER,
                constants.UserTypeNames.STAFF,
            ]:
                site_objects = (
                    user_controller.get_sites_by_user_and_company_ids(
                        user=user, company_ids=company_ids
                    )
                )

        serialized_data = user_serializers.SiteSerializer(
            site_objects, many=True
        ).data
        return response.Response(
            {
                "result": True,
                "msg": "Success",
                "data": serialized_data,
            },
            status=status.HTTP_200_OK,
        )


class SignIn(views.APIView):
    """
    API endpoint to handle user signin requests
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user, token = signin.sign_in(request=request)
        data = {
            "user_id": user.id,
            "user_type_id": user.userprofiledetails.user_type.id,
            "user_type": user.userprofiledetails.user_type.name,
            "token": token.key,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "country_code": user.userprofiledetails.country_code,
            "mobile_number": user.userprofiledetails.mobile_number,
            "designation_id": user.userprofiledetails.designation_id,
            "site_address": user.userprofiledetails.site_address,
        }

        return response.Response(
            {"result": True, "msg": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class Logout(views.APIView):
    """
    API endpoint to handle user logout requests
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return signout.logout(request=request)


class ForgotPassword(views.APIView):
    """
    API endpoint to handle forgot password requests from user.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return forgot_password.forgot_password(request=request)


class ChangePassword(views.APIView):
    """
    Setting password for user after approving uconnect admin.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token", "")
        password = request.data.get("password", "")
        confirm_password = request.data.get("confirm_password", "")
        validator.ResetPassword(
            token=token, password=password, confirm_password=confirm_password
        )
        user_controller = controllers.UserController()
        result = user_controller.set_user_password(
            token=token, password=password, confirm_password=confirm_password
        )

        if result:
            return response.Response(
                {
                    "result": True,
                    "msg": "Your password has been successfully reset. You can now log in with your new password.",
                },
                status=status.HTTP_200_OK,
            )
        return response.Response(
            {
                "result": False,
                "msg": "Invalid Token to change the password",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request):
        token = request.query_params.get("token", "")
        if not token:
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid or expired password reset link. Please initiate the forgot password process again.",
                    "validation_error_field": "token",
                    "validation_error_msg": "Invalid URL - Token missing or empty.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        result, data = encrypt_decrypt.decrypt(token)
        if result:
            email, token_datetime_str = str(data).split("^^^")
            user_controller = controllers.UserController()
            user_controller.check_password_reset_token(
                token=token, token_datetime_str=token_datetime_str
            )

            return response.Response(
                {
                    "result": True,
                    "msg": "Token is valid",
                },
                status=status.HTTP_200_OK,
            )
        return response.Response(
            {
                "result": False,
                "msg": "Invalid or expired password reset link. Please initiate the forgot password process again.",
                "validation_error_field": "token",
                "validation_error_msg": "Invalid Token",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserInvite(views.APIView):
    """
    API endpoint to handle company user invite requests
    """

    def post(self, request):
        user = request.user
        data = request.data
        email = data.get("email", "").strip().lower()
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        site_list = data.get("site_list", "")
        user_type_id = data.get("user_type_id", "")

        user_controller = controllers.UserController()
        user_profile = user_controller.get_user_profile_by_user(user=user)
        if not user_profile.user_type.id == constants.UserTypeNames.ADMIN:
            return response.Response(
                {
                    "result": False,
                    "msg": "Only Admin can invite users",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not email:
            return response.Response(
                {
                    "result": False,
                    "msg": "Email ID cannot be empty. Please provide a valid email address.",
                    "validation_error_field": "email",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not first_name:
            return response.Response(
                {
                    "result": False,
                    "msg": "First name cannot be empty. Please provide a valid first name.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(first_name) < 2:
            return response.Response(
                {
                    "result": False,
                    "msg": "Please enter a valid first name with more than one character.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(first_name) > 50:
            return response.Response(
                {
                    "result": False,
                    "msg": "First Name exceeds the maximum length of 50 characters.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not first_name.isalpha():
            return response.Response(
                {
                    "result": False,
                    "msg": "First Name should only contain alphabetic characters.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not last_name:
            return response.Response(
                {
                    "result": False,
                    "msg": "Last name cannot be empty. Please provide a valid last name.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(last_name) < 2:
            return response.Response(
                {
                    "result": False,
                    "msg": "Please enter a valid last name with more than one character.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(last_name) > 50:
            return response.Response(
                {
                    "result": False,
                    "msg": "Last Name exceeds the maximum length of 50 characters.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not last_name.isalpha():
            return response.Response(
                {
                    "result": False,
                    "msg": "Last Name should only contain alphabetic characters.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user_type_id:
            return response.Response(
                {
                    "result": False,
                    "msg": "User type id is required",
                    "validation_error_field": "user_type",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(user_type_id).isdigit() is False:
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid User Type",
                    "validation_error_field": "user_type",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_type_id not in [
            constants.UserTypeNames.STAFF,
            constants.UserTypeNames.CUSTOMER,
        ]:
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid user type id",
                    "validation_error_field": "user_type",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # site_list = [item["site_id"] for item in site_list]
        site_list = list(map(lambda x: x["site_id"], site_list))

        is_existing_email = user_controller.check_if_email_already_exists(
            email=email
        )

        if is_existing_email:
            existing_user = user_controller.get_existing_user(email=email)

            if existing_user.is_active is True:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Active user already exists for this email address",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if existing_user.userprofiledetails.user_type_id != user_type_id:
                message = (
                    "Email already in use for customer; staff email must be unique for sending invites."
                    if user_type_id == constants.UserTypeNames.STAFF
                    else "Email already in use for staff; customer email must be unique for sending invites."
                )
                return response.Response(
                    {
                        "result": False,
                        "msg": message,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data = {
                "user_id": existing_user.id,
                "is_email_already_sent": True,
            }
            return response.Response(
                {
                    "result": True,
                    "msg": "The email appears to have already been sent. Would you like the invite email to be resent?",
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )

        else:
            user_profile = user_controller.user_invite(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                site_list=site_list,
                user_type_id=user_type_id,
            )

        user_controller.create_and_send_invite_mail(user_profile=user_profile)

        serialized_data = user_serializers.UserSerializer(
            instance=user_profile, many=False
        ).data

        return response.Response(
            {
                "result": True,
                "msg": "User invited successfully. An email invitation has been sent.",
                "data": serialized_data,
            },
            status=status.HTTP_201_CREATED,
        )


class ResendInviteMail(views.APIView):
    """
    API endpoint to resend invite mail for existing users who haven't signed up yet.
    """

    def post(self, request):
        admin_user = request.user
        data = request.data
        is_quick_resend = data.get("is_quick_resend", False)
        user_id = data.get("user_id", "")
        user_type_id = data.get("user_type_id", "")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        site_list = data.get("site_list", [])

        user_controller = controllers.UserController()
        user_profile = user_controller.get_user_profile_by_user(
            user=admin_user
        )
        if not user_profile.user_type.id == constants.UserTypeNames.ADMIN:
            return response.Response(
                {
                    "result": False,
                    "msg": "Only Admin have access to this API.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        existing_user = user_controller.get_user_with_user_profile_by_id(
            user_id=user_id
        )

        if is_quick_resend:
            user_controller.create_and_send_invite_mail(
                user_profile=existing_user.userprofiledetails
            )

        else:
            user_profile = user_controller.user_invite_with_existing_user(
                admin_user=admin_user,
                existing_user=existing_user,
                first_name=first_name,
                last_name=last_name,
                site_list=site_list,
                user_type_id=user_type_id,
            )
            user_controller.create_and_send_invite_mail(
                user_profile=user_profile
            )

        serialized_data = user_serializers.UserSerializer(
            instance=existing_user.userprofiledetails, many=False
        ).data

        return response.Response(
            {
                "result": True,
                "msg": "User invited successfully. An email invitation has been sent.",
                "data": serialized_data,
            },
            status=status.HTTP_200_OK,
        )


class UserMaster(views.APIView):
    """
    API endpoint to handle staff, Customer users.
    """

    def get(self, request):
        admin_or_staff_user = request.user
        user_controller = controllers.UserController()
        admin_or_staff_user_profile = user_controller.get_user_profile_by_user(
            user=admin_or_staff_user
        )
        if not (
            admin_or_staff_user_profile.user_type.id
            in [constants.UserTypeNames.ADMIN, constants.UserTypeNames.STAFF]
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Only Admin and Staff have access to this API.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        query_params = request.query_params
        user_id = query_params.get("user_id", None)
        user_type_id = query_params.get("user_type_id", "")
        search_text = query_params.get("search_text", "")
        company_filter_str = query_params.get("company_filter", "[]")
        site_filter_str = query_params.get("site_filter", "[]")
        first_name_sort = query_params.get("first_name_sort", "0")
        last_name_sort = query_params.get("last_name_sort", "0")
        company_sort = query_params.get("company_sort", "0")
        site_sort = query_params.get("site_sort", "0")
        limit = query_params.get("limit", "")
        offset = query_params.get("offset", "0")

        if user_id:
            if not user_id.isdigit():
                return response.Response(
                    {
                        "result": False,
                        "msg": "Invalid user id",
                        "validation_error_field": "user_id",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = user_controller.get_user_with_profile_and_site_by_id(
                user_id=user_id
            )
            serialized_data = user_serializers.UserDetailSerializer(user).data

            return response.Response(
                {
                    "result": True,
                    "msg": "Success",
                    "data": serialized_data,
                },
                status=status.HTTP_200_OK,
            )

        if not user_type_id:
            return response.Response(
                {
                    "result": False,
                    "msg": "User type id is required",
                    "validation_error_field": "user_type",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user_type_id.isdigit():
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid user type id",
                    "validation_error_field": "user_type_id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if int(user_type_id) not in [
            constants.UserTypeNames.STAFF,
            constants.UserTypeNames.CUSTOMER,
        ]:
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid user type id",
                    "validation_error_field": "user_type",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not first_name_sort.isdigit()
            or int(first_name_sort)
            not in constants.SORT_ORDER_OPTIONS.values()
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid first name sort",
                    "validation_error_field": "first_name_sort",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not last_name_sort.isdigit()
            or int(last_name_sort) not in constants.SORT_ORDER_OPTIONS.values()
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid last name sort",
                    "validation_error_field": "last_name_sort",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not company_sort.isdigit()
            or int(company_sort) not in constants.SORT_ORDER_OPTIONS.values()
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid company sort",
                    "validation_error_field": "company_sort",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not site_sort.isdigit()
            or int(site_sort) not in constants.SORT_ORDER_OPTIONS.values()
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid site sort",
                    "validation_error_field": "site_sort",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        company_filter = []
        if company_filter_str and str(company_filter_str).isdigit() is False:
            try:
                teststr = f"{company_filter_str}"
                company_filter = ast.literal_eval(teststr)
            except Exception:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Invalid company filter.",
                        "validation_error_field": "company_filter",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        site_filter = []
        if site_filter_str and str(site_filter_str).isdigit() is False:
            try:
                teststr = f"{site_filter_str}"
                site_filter = ast.literal_eval(teststr)
            except Exception:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Invalid site filter.",
                        "validation_error_field": "site_filter",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        user_objects = user_controller.get_all_users(
            user_type_id=int(user_type_id)
        )
        if search_text:
            user_objects = user_controller.get_user_objects_by_search(
                user_objects=user_objects, search_text=search_text
            )
            if len(user_objects) == 0:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Sorry, no results found for your search.",
                    },
                    status=status.HTTP_200_OK,
                )

        if company_filter:
            user_objects = user_controller.get_user_objects_by_company(
                user_objects=user_objects, company_filter=company_filter
            )

        if site_filter:
            user_objects = user_controller.get_user_objects_by_site(
                user_objects=user_objects, site_filter=site_filter
            )

        user_objects_count = len(user_objects)

        if int(first_name_sort):
            user_objects = user_controller.get_user_objects_first_name_sorted(
                user_objects=user_objects,
                first_name_sort=("first_name", int(first_name_sort)),
            )

        if int(last_name_sort):
            user_objects = user_controller.get_user_objects_last_name_sorted(
                user_objects=user_objects,
                last_name_sort=("last_name", int(last_name_sort)),
            )

        if int(company_sort):
            user_objects = user_controller.get_user_objects_company_sorted(
                user_objects=user_objects,
                company_sort=("company_name", int(company_sort)),
            )

        if int(site_sort):
            user_objects = user_controller.get_user_objects_site_sorted(
                user_objects=user_objects,
                site_sort=("site_name", int(site_sort)),
            )

        if not limit:
            return response.Response(
                {
                    "result": False,
                    "msg": "Limit is required",
                    "validation_error_field": "limit",
                }
            )

        (user_objects, next_link,) = user_controller.get_paginated_response(
            queryset=user_objects,
            offset=offset,
            limit=limit,
        )

        return response.Response(
            {
                "result": True,
                "msg": "Success",
                "next_link": next_link,
                "user_count": user_objects_count,
                "data": user_objects,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        admin_user = request.user
        user_controller = controllers.UserController()
        admin_user_profile = user_controller.get_user_profile_by_user(
            user=admin_user
        )
        if (
            not admin_user_profile.user_type.id
            == constants.UserTypeNames.ADMIN
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Only Admin has access to this API.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        data = request.data
        user_id = data.get("user_id", "")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        designation_id = data.get("designation_id", "")
        others_designation_name = data.get("others_designation_name", "")
        site_address = data.get("site_address", "")
        site_list = data.get("site_list", None)

        if not user_id:
            return response.Response(
                {
                    "result": False,
                    "msg": "User id is required",
                    "validation_error_field": "user_id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not first_name:
            return response.Response(
                {
                    "result": False,
                    "msg": "First name cannot be empty. Please provide a valid first name.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(first_name) < 2:
            return response.Response(
                {
                    "result": False,
                    "msg": "Please enter a valid first name with more than one character.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(first_name) > 50:
            return response.Response(
                {
                    "result": False,
                    "msg": "First Name exceeds the maximum length of 50 characters.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not first_name.isalpha():
            return response.Response(
                {
                    "result": False,
                    "msg": "First Name should only contain alphabetic characters.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not last_name:
            return response.Response(
                {
                    "result": False,
                    "msg": "Last name cannot be empty. Please provide a valid last name.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(last_name) < 2:
            return response.Response(
                {
                    "result": False,
                    "msg": "Please enter a valid last name with more than one character.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(last_name) > 50:
            return response.Response(
                {
                    "result": False,
                    "msg": "Last Name exceeds the maximum length of 50 characters.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not last_name.isalpha():
            return response.Response(
                {
                    "result": False,
                    "msg": "Last Name should only contain alphabetic characters.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if designation_id:
            try:
                designation_object = models.DesignationMaster.objects.get(
                    id=designation_id, is_active=True
                )
            except exceptions.ObjectDoesNotExist:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Invalid Designation.",
                        "validation_error_field": "desingation",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if designation_object.id == constants.DesignationNames.OTHERS:
                if not others_designation_name:
                    return response.Response(
                        {
                            "result": False,
                            "msg": "Designation cannot be empty. Please provide a valid designation.",
                            "validation_error_field": "others_designation_name",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if len(others_designation_name) < 2:
                    return response.Response(
                        {
                            "result": False,
                            "msg": " Please enter a valid designation with more than one character.",
                            "validation_error_field": "others_designation_name",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if len(others_designation_name) > 60:
                    return response.Response(
                        {
                            "result": False,
                            "msg": "Designation exceeds the maximum length of 60 characters.",
                            "validation_error_field": "others_designation_name",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not others_designation_name.replace(" ", "").isalpha():
                    return response.Response(
                        {
                            "result": False,
                            "msg": "Please enter a valid designation without numeric or special characters.",
                            "validation_error_field": "others_designation_name",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                others_designation_name = ""
        else:
            designation_object = None
            others_designation_name = ""

        if site_address and len(site_address) > 200:
            return response.Response(
                {
                    "result": False,
                    "msg": "Site Address exceeds the maximum length of 200 characters.",
                    "validation_error_field": "site_address",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if site_list is None:
            return response.Response(
                {
                    "result": False,
                    "msg": "Site list is required",
                    "validation_error_field": "site_list",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        site_list = [item["site_id"] for item in site_list]

        user = user_controller.get_user_with_profile_and_site_by_id(
            user_id=user_id
        )
        user.first_name = first_name
        user.last_name = last_name
        user.userprofiledetails.designation = designation_object
        user.userprofiledetails.others_designation_name = (
            others_designation_name
        )
        user.userprofiledetails.site_address = site_address

        usersitemappings = user.usersitemapping_set.all()
        user = user_controller.update_user_site_mappings(
            user=user, usersitemappings=usersitemappings, site_list=site_list
        )

        if (
            user.userprofiledetails.site_preference_id is not None
            and user.userprofiledetails.site_preference_id not in site_list
        ):
            user.userprofiledetails.site_preference_id = None

        user.userprofiledetails.save()
        user.save()

        data = {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "designation_id": user.userprofiledetails.designation_id,
            "others_designation_name": user.userprofiledetails.others_designation_name,
            "site_address": user.userprofiledetails.site_address,
        }
        return response.Response(
            {
                "result": True,
                "msg": "User details have been successfully updated.",
                "data": data,
            },
            status=status.HTTP_200_OK,
        )


class ToggleUserSiteMapping(views.APIView):
    """
    API endpoint to handle disabling of user site mapping record
    """

    def put(self, request):
        admin_user = request.user
        user_controller = controllers.UserController()
        admin_user_profile = user_controller.get_user_profile_by_user(
            user=admin_user
        )
        if not (
            admin_user_profile.user_type.id == constants.UserTypeNames.ADMIN
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Only Admin has access to this API.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        data = request.data
        user_id = data.get("user_id", "")
        user_site_mapping_id = data.get("user_site_mapping_id", None)
        is_active = data.get("is_active", None)

        if not user_id:
            return response.Response(
                {
                    "result": False,
                    "msg": "User site mapping id is required",
                    "validation_error_field": "user_site_mapping_id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if is_active is None:
            return response.Response(
                {
                    "result": False,
                    "msg": "is_active is required",
                    "validation_error_field": "is_active",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_profile = user_controller.get_user_profile_by_user_id(
            user_id=user_id
        )

        if user_site_mapping_id is not None:
            user_site_mapping_object = (
                user_controller.get_user_site_mapping_by_id(
                    user_site_mapping_id=user_site_mapping_id
                )
            )
            user_site_mapping_object.is_active = is_active
            if (
                not is_active
                and user_profile.site_preference is not None
                and user_profile.site_preference_id
                == user_site_mapping_object.site_id
            ):
                user_profile.site_preference = None
            user_site_mapping_object.save()

            user_site_mappings = (
                user_controller.get_user_site_mappings_by_user(
                    user=user_profile.user
                )
            )
            if not user_site_mappings.exists():
                user_profile.is_disabled = True

            else:
                user_profile.is_disabled = False

            user_profile.save()

            return response.Response(
                {
                    "result": True,
                    "msg": "Updated Successfully",
                    "data": {
                        "user_id": user_profile.user.id,
                        "user_site_mapping_id": user_site_mapping_object.id,
                        "is_active": user_site_mapping_object.is_active,
                        "is_user_disabled": user_profile.is_disabled,
                    },
                },
                status=status.HTTP_200_OK,
            )
        else:
            user_profile.is_disabled = not is_active
            user_profile.save()
            return response.Response(
                {
                    "result": True,
                    "msg": "User account updated Successfully",
                    "data": {
                        "user_id": user_profile.user.id,
                        "is_active": is_active,
                        "is_user_disabled": user_profile.is_disabled,
                    },
                },
                status=status.HTTP_200_OK,
            )


class ExportToCSV(views.APIView):
    """
    API endpoint to handle exporting user site mapping to csv
    """

    def get(self, request):
        admin_or_staff_user = request.user
        user_controller = controllers.UserController()
        admin_or_staff_user_profile = user_controller.get_user_profile_by_user(
            user=admin_or_staff_user
        )
        if not (
            admin_or_staff_user_profile.user_type.id
            in [constants.UserTypeNames.ADMIN, constants.UserTypeNames.STAFF]
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Only Admin and Staff have access to this API.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        query_params = request.query_params
        user_type_id = query_params.get("user_type_id", "")
        search_text = query_params.get("search_text", "")
        company_filter_str = query_params.get("company_filter", "[]")
        site_filter_str = query_params.get("site_filter", "[]")
        first_name_sort = query_params.get("first_name_sort", "0")
        last_name_sort = query_params.get("last_name_sort", "0")
        company_sort = query_params.get("company_sort", "0")
        site_sort = query_params.get("site_sort", "0")
        limit = query_params.get("limit", "")
        offset = query_params.get("offset", "0")

        if not user_type_id:
            return response.Response(
                {
                    "result": False,
                    "msg": "User type id is required",
                    "validation_error_field": "user_type",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user_type_id.isdigit():
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid user type id",
                    "validation_error_field": "user_type_id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if int(user_type_id) not in [
            constants.UserTypeNames.STAFF,
            constants.UserTypeNames.CUSTOMER,
        ]:
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid user type id",
                    "validation_error_field": "user_type",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not first_name_sort.isdigit()
            or int(first_name_sort)
            not in constants.SORT_ORDER_OPTIONS.values()
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid first name sort",
                    "validation_error_field": "first_name_sort",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not last_name_sort.isdigit()
            or int(last_name_sort) not in constants.SORT_ORDER_OPTIONS.values()
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid last name sort",
                    "validation_error_field": "last_name_sort",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not company_sort.isdigit()
            or int(company_sort) not in constants.SORT_ORDER_OPTIONS.values()
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid company sort",
                    "validation_error_field": "company_sort",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not site_sort.isdigit()
            or int(site_sort) not in constants.SORT_ORDER_OPTIONS.values()
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid site sort",
                    "validation_error_field": "site_sort",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        company_filter = []
        if company_filter_str and str(company_filter_str).isdigit() is False:
            try:
                teststr = f"{company_filter_str}"
                company_filter = ast.literal_eval(teststr)
            except Exception:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Invalid company filter.",
                        "validation_error_field": "company_filter",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        site_filter = []
        if site_filter_str and str(site_filter_str).isdigit() is False:
            try:
                teststr = f"{site_filter_str}"
                site_filter = ast.literal_eval(teststr)
            except Exception:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Invalid site filter.",
                        "validation_error_field": "site_filter",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        user_objects = user_controller.get_all_users(
            user_type_id=int(user_type_id)
        )
        if search_text:
            user_objects = user_controller.get_user_objects_by_search(
                user_objects=user_objects, search_text=search_text
            )

        if company_filter:
            user_objects = user_controller.get_user_objects_by_company(
                user_objects=user_objects, company_filter=company_filter
            )

        if site_filter:
            user_objects = user_controller.get_user_objects_by_site(
                user_objects=user_objects, site_filter=site_filter
            )

        if int(first_name_sort):
            user_objects = user_controller.get_user_objects_first_name_sorted(
                user_objects=user_objects,
                first_name_sort=("first_name", int(first_name_sort)),
            )

        if int(last_name_sort):
            user_objects = user_controller.get_user_objects_last_name_sorted(
                user_objects=user_objects,
                last_name_sort=("last_name", int(last_name_sort)),
            )

        if int(company_sort):
            user_objects = user_controller.get_user_objects_company_sorted(
                user_objects=user_objects,
                company_sort=("company_name", int(company_sort)),
            )

        if int(site_sort):
            user_objects = user_controller.get_user_objects_site_sorted(
                user_objects=user_objects,
                site_sort=("site_name", int(site_sort)),
            )

        (
            has_non_blank_others_designation,
            user_objects,
        ) = user_controller.convert_user_objects_to_list_for_csv(
            user_type_id=int(user_type_id), user_objects=user_objects
        )

        if not limit:
            return response.Response(
                {
                    "result": False,
                    "msg": "Limit is required",
                    "validation_error_field": "limit",
                }
            )

        (user_objects, next_link,) = user_controller.get_paginated_response(
            queryset=user_objects,
            offset=offset,
            limit=limit,
        )

        file_name = (
            "staff_data_"
            if int(user_type_id) == constants.UserTypeNames.STAFF
            else "customer_data_"
        )
        file_name += datetime.datetime.now().strftime(constants.DATE_FORMAT)
        file_name += ".csv"

        response_data = HttpResponse(content_type="text/csv")
        response_data[
            "Content-Disposition"
        ] = f"attachment; filename={file_name}"
        writer = csv.writer(response_data)
        headers = [
            "First name",
            "Last name",
            "Email",
            "Mobile number",
            "Company",
            "Site",
            "Designation",
        ]
        if has_non_blank_others_designation:
            headers.extend(["Other designation name"])
        headers.extend(
            ["Site Address", "Date joined"]
            if int(user_type_id) == constants.UserTypeNames.CUSTOMER
            else ["Date joined"]
        )
        writer.writerow(headers)
        for object in user_objects:
            date_joined = (
                object[-1].strftime(constants.DATE_FORMAT)
                if isinstance(object[-1], datetime.date)
                else object[-1]
            )
            row = list(object[:-1]) + [date_joined]
            writer.writerow(row)
        return response_data


class UserProfile(views.APIView):

    """
    API endpoint to handle user profile personal information updates.
    """

    def put(self, request):
        user = request.user
        data = request.data

        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        country_code = data.get("country_code", "")
        mobile_number = data.get("mobile_number", "")
        email = data.get("email", "").strip().lower()
        designation_id = data.get("designation_id", None)
        others_designation_name = data.get("others_designation_name", "")
        common_controller = controllers.CommonController()
        user_controller = controllers.UserController()
        user_profile = user_controller.get_user_profile_by_user(user=user)

        if not first_name:
            return response.Response(
                {
                    "result": False,
                    "msg": "First name cannot be empty. Please provide a valid first name.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(first_name) < 2:
            return response.Response(
                {
                    "result": False,
                    "msg": "Please enter a valid first name with more than one character.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(first_name) > 50:
            return response.Response(
                {
                    "result": False,
                    "msg": "First Name exceeds the maximum length of 50 characters.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not first_name.isalpha():
            return response.Response(
                {
                    "result": False,
                    "msg": "First Name should only contain alphabetic characters.",
                    "validation_error_field": "first_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not last_name:
            return response.Response(
                {
                    "result": False,
                    "msg": "Last name cannot be empty. Please provide a valid last name.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(last_name) < 2:
            return response.Response(
                {
                    "result": False,
                    "msg": "Please enter a valid last name with more than one character.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(last_name) > 50:
            return response.Response(
                {
                    "result": False,
                    "msg": "Last Name exceeds the maximum length of 50 characters.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not last_name.isalpha():
            return response.Response(
                {
                    "result": False,
                    "msg": "Last Name should only contain alphabetic characters.",
                    "validation_error_field": "last_name",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if mobile_number:
            if not country_code:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Country code missing or empty.",
                        "validation_error_field": "country_code",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not re.match(r"^[0-9]{10}$", mobile_number):
                return response.Response(
                    {
                        "result": False,
                        "msg": "Please enter a valid mobile number.",
                        "validation_error_field": "mobile_nubmer",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if designation_id:
            try:
                designation_object = models.DesignationMaster.objects.get(
                    id=designation_id, is_active=True
                )
            except exceptions.ObjectDoesNotExist:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Invalid Designation.",
                        "validation_error_field": "desingation",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if designation_object.id == constants.DesignationNames.OTHERS:
                if not others_designation_name:
                    return response.Response(
                        {
                            "result": False,
                            "msg": "Designation cannot be empty. Please provide a valid designation.",
                            "validation_error_field": "others_designation_name",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if len(others_designation_name) < 2:
                    return response.Response(
                        {
                            "result": False,
                            "msg": " Please enter a valid designation with more than one character.",
                            "validation_error_field": "others_designation_name",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if len(others_designation_name) > 60:
                    return response.Response(
                        {
                            "result": False,
                            "msg": "Designation exceeds the maximum length of 60 characters.",
                            "validation_error_field": "others_designation_name",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not others_designation_name.replace(" ", "").isalpha():
                    return response.Response(
                        {
                            "result": False,
                            "msg": "Please enter a valid designation without numeric or special characters.",
                            "validation_error_field": "others_designation_name",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                others_designation_name = ""
        else:
            designation_object = None
            others_designation_name = ""

        if not email:
            return response.Response(
                {
                    "result": False,
                    "msg": "Email ID cannot be empty. Please provide a valid email address.",
                    "validation_error_field": "email",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_email_updated = False
        if email != user.email:
            common_controller.is_valid_email(email=email)
            is_existing_email = user_controller.check_if_email_already_active(
                email=email
            )
            if is_existing_email:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Email ID already exists for another user.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_profile.new_email = email
            token = send_verification_mail.send_mail(
                user_id=user.id,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user_profile.is_email_verified = False
            common_controller.add_token_to_reset_token_log(
                user=user, token=token
            )
            is_email_updated = True

        if email != user_profile.new_email:
            user_profile.new_email = email
            user_profile.is_email_verified = True

        user.first_name = first_name
        user.last_name = last_name

        user_profile.country_code = country_code
        user_profile.mobile_number = mobile_number
        if user_profile.user_type.id in [
            constants.UserTypeNames.STAFF,
            constants.UserTypeNames.CUSTOMER,
        ]:
            user_profile.designation = designation_object
            user_profile.others_designation_name = others_designation_name

        user.save()
        user_profile.save()

        data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "old_email": user.email,
            "new_email": user_profile.new_email,
            "is_email_verified": user_profile.is_email_verified,
            "country_code": user_profile.country_code,
            "mobile_number": user_profile.mobile_number,
            "designation_id": user_profile.designation_id,
            "others_designation_name": user_profile.others_designation_name,
        }
        return response.Response(
            {
                "result": True,
                "msg": "Your profile information has been updated successfully.",
                "is_email_updated": is_email_updated,
                "data": data,
            },
            status=status.HTTP_200_OK,
        )

    def get(self, request):
        user = request.user

        user_controller = controllers.UserController()

        user_profile = user_controller.get_user_profile_with_site_by_user(
            user=user
        )

        serialized_data = user_serializers.UserProfileDetailSerializer(
            instance=user_profile
        ).data

        return response.Response(
            {
                "result": True,
                "msg": "Success",
                "data": serialized_data,
            },
            status=status.HTTP_200_OK,
        )


class EmailVerification(views.APIView):
    """
    API endpoint to handle email verification requests from verfication link sent to user email
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query_params = request.query_params

        verify_token = query_params.get("verify_token", "")

        if not verify_token:
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid URL - Token Missing or Empty",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        result, data = encrypt_decrypt.decrypt(verify_token)
        common_controller = controllers.CommonController()
        user_controller = controllers.UserController()
        if result:
            token_user_id, token_email, token_datetime_str = str(data).split(
                "^^^"
            )

            token_log = common_controller.check_token_expired(
                token=verify_token
            )
            if token_log is None:
                return response.Response(
                    {
                        "result": False,
                        "msg": "The verification link has expired or is invalid. Please request a new verification link.",
                        "validation_error_field": "token",
                        "validation_error_message": "Expired token",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            is_token_timeout = common_controller.check_token_timeout_expired(
                token_datetime_str=token_datetime_str
            )
            if is_token_timeout:
                token_log.is_expired = True
                token_log.token = ""
                token_log.save()
                return response.Response(
                    {
                        "result": False,
                        "msg": "The verification link has expired or is invalid. Please request a new verification link.",
                        "validation_error_field": "token",
                        "validation_error_message": "Time Out Expired token",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            is_email_active = user_controller.check_if_email_already_active(
                email=token_email
            )

            if is_email_active:
                token_log.is_expired = True
                token_log.token = ""
                token_log.save()
                return response.Response(
                    {
                        "result": False,
                        "msg": "Email is already active for another user",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_profile_details = user_controller.get_user_profile_by_id(
                user_id=int(token_user_id),
                email=token_email,
                token_log=token_log,
            )
            if user_profile_details.is_email_verified is True:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Email already verified",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_profile_details.user.email = user_profile_details.new_email
            user_profile_details.user.username = user_profile_details.new_email
            user_profile_details.is_email_verified = True

            user_profile_details.user.save()
            user_profile_details.save()
            token_log.is_expired = True
            token_log.token = ""
            token_log.save()

            return response.Response(
                {
                    "result": True,
                    "msg": "Your email address has been successfully verified. You can now use your new email address to log in.",
                },
                status=status.HTTP_200_OK,
            )

        return response.Response(
            {
                "result": False,
                "msg": "Invalid Token verification request",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserProfileSitePreference(views.APIView):
    """
    API endpoint to handle setting site preference by a user in user profile.
    """

    def put(self, request):
        user = request.user
        data = request.data

        user_controller = controllers.UserController()
        user_profile = user_controller.get_user_profile_by_user(user=user)

        site_id = data.get("site_id", None)

        if not site_id:
            return response.Response(
                {
                    "result": False,
                    "msg": "site id missing or empty",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if type(site_id) is not int:
            return response.Response(
                {
                    "result": False,
                    "msg": "site id should be an integer",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_controller = controllers.UserController()
        user_profile = user_controller.get_user_profile_by_user(user=user)
        site = user_controller.get_site_by_id(site_id=site_id)
        if user_profile.user_type.id in [
            constants.UserTypeNames.STAFF,
            constants.UserTypeNames.CUSTOMER,
        ]:
            user_controller.check_user_site_mapping(user=user, site=site)
        user_profile.site_preference = site
        user_profile.save()

        return response.Response(
            {
                "result": True,
                "msg": "Site preference updated successfully.",
                "user_id": user.id,
                "preference_company_id": user_profile.site_preference.company.id,
                "preference_company_name": user_profile.site_preference.company.name,
                "preference_site_id": user_profile.site_preference.id,
                "preference_site_name": user_profile.site_preference.name,
            },
            status=status.HTTP_200_OK,
        )


class UserProfileChangePassword(views.APIView):
    """
    API endpoint to handle change password request  in user profile.
    """

    def put(self, request):
        user = request.user
        data = request.data

        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        confirm_password = data.get("confirm_password", "")

        validator.ChangePassword(
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
        )

        user_controller = controllers.UserController()

        if not user.check_password(raw_password=current_password):
            return response.Response(
                {
                    "result": False,
                    "msg": "Invalid current password. Please check your current password and try again.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return response.Response(
                {
                    "result": False,
                    "msg": "Confirm password does not match the new password.",
                    "validation_error_field": "confirm_password",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_controller.password_history_check(
            user=user, password=new_password
        )
        user_controller.change_password(user=user, password=new_password)

        return response.Response(
            {
                "result": "True",
                "msg": "Your password has been updated successfully.",
            }
        )


class UploadProfilePic(views.APIView):
    """
    API endpoint to handle upload and remove profile pictures in user profile.
    """

    parser_classes = [parsers.MultiPartParser]

    def post(self, request):
        user = request.user
        data = request.data

        profile_pic = data.get("profile_pic", "")

        user_controller = controllers.UserController()

        user_profile_details = user_controller.get_user_profile_by_user(
            user=user
        )
        if profile_pic == "":
            data = {
                "thumbnail_profile_pic": "",
                "medium_profile_pic": "",
                "profile_pic": "",
            }

        else:
            ext = str(profile_pic.name).split(".")[-1]
            if ext not in constants.IMAGE_EXT:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Invalid image format. Please upload a supported image format (e.g., JPG, PNG)",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            profile = user_profile.update_profile_pic(
                image=profile_pic, user=user, user_profile=user_profile_details
            )
            data = {
                "thumbnail_profile_pic": profile.thumbnail_profile_pic.url,
                "medium_profile_pic": profile.medium_profile_pic.url,
                "profile_pic": profile.profile_pic.url,
            }

        return response.Response(
            {
                "result": True,
                "msg": "Profile picture has been changed successfully.",
                "data": data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        user = request.user

        user_controller = controllers.UserController()
        user_profile_details = user_controller.get_user_profile_by_user(
            user=user
        )

        user_profile_details.thumbnail_profile_pic = ""
        user_profile_details.medium_profile_pic = ""
        user_profile_details.profile_pic = ""

        user_profile_details.save()

        return response.Response(
            {
                "result": True,
                "msg": "Profile pic removed successfully",
            },
            status=status.HTTP_200_OK,
        )
