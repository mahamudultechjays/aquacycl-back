import datetime
import secrets
import string
import typing

from django.contrib import auth
from django.contrib.auth.hashers import check_password
from django.core import exceptions, validators
from django.db import models as django_models
from django.db.models import Case, F, Prefetch, Q, Value, When
from django.db.models.functions import Coalesce, Concat
from rest_framework import serializers

from aquacycl_project import constants, settings
from tj_packages import encrypt_decrypt
from users import mailing, models

User = auth.get_user_model()


class CommonController:
    """
    To check if the user has verified the email via verification link
    Params:
        token: str,
    Returns:
        is_valid: data decrypted from verifytoken sent along with verification link
    """

    def is_valid_email(self, email: str):
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

    def generate_password(
        self,
    ) -> str:
        """
        Generates and returns a random password.

        Returns:
        String, a randomly generated string
        """

        password = "".join(
            secrets.choice(string.ascii_uppercase + string.digits)
            for i in range(12)
        )
        return password

    def is_email_exist(self, email: str):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Email address already exists",
                    "validation_error_field": "email",
                },
                code="validation_error",
            )

    def add_token_to_reset_token_log(self, user: models.User, token: str):
        """
        Adds the generated token for signup invite, reset password and email verification to the reset token log
        Params:
            user: User object
            token: The generated token for signup invite, reset password and email verification
        """
        models.ResetTokenLog.objects.create(user=user, token=token)

    def verify_authorization_token(self, token: str) -> bool:
        if not token:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid Request",
                },
                code="validation_error",
            )
        is_valid = encrypt_decrypt.decrypt(token)[0]
        if not is_valid:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid Request",
                },
                code="validation_error",
            )
        return is_valid

    def check_token_expired(
        self,
        token: str,
    ) -> typing.Union[models.ResetTokenLog, None]:
        """
        Checking the token already used or not.
        Params:
            token: token provided in queryparams of reset password, signup and email verification link,
        Returns:
            token_log: Instance of ResetTokenLog or None
        """

        return models.ResetTokenLog.objects.filter(
            token=token, is_expired=False
        ).first()

    def check_token_timeout_expired(
        self,
        token_datetime_str: str,
    ) -> bool:
        """
        To check whether the given token datetime string is expired based on current datetime
        Params:
            token_datetime_str: token datetime string
        Returns:
            bool: True if token datetime string is expired, False otherwise
        """
        current_datetime = datetime.datetime.utcnow()
        token_datetime = datetime.datetime.strptime(
            token_datetime_str, constants.DATE_TIME_FORMAT
        )
        time_difference = current_datetime - token_datetime
        return time_difference > datetime.timedelta(hours=24)


class UserController:
    def user_invite(
        self,
        user: User,
        email: str,
        first_name: str,
        last_name: str,
        site_list: list,
        user_type_id: int,
    ) -> models.UserProfileDetails:
        """
        Creates a new user profile for the invited user based on data given by the admin
        params:
            user: the user who initiated the invite request
            email: the email of the invited user
            first_name: the first name of the invited user
            last_name: the last name of the invited user
            company_list: the list of associated companies of the invited user
            user_type_id: the type of the invited user, either staff or customer
        returns:
            user_profile: the newly created user profile for the invited user
        """
        CommonController().is_valid_email(email=email)
        # CommonController().is_email_exist(email=email)

        invited_user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=email,
            email=email,
            is_active=False,
        )
        password = CommonController().generate_password()
        if invited_user:
            invited_user.set_password(password)
            invited_user.save()

        user_profile = models.UserProfileDetails.objects.create(
            user=invited_user,
            user_type_id=user_type_id,
            new_email=email,
            is_active=False,
        )

        models.InviteUser.objects.create(
            user=user,
            invited_user=invited_user,
        )

        user_site_mapping_objects = []
        if site_list:
            for site in site_list:
                user_site_mapping_objects.append(
                    models.UserSiteMapping(
                        user=invited_user,
                        site_id=site,
                        is_active=True,
                    )
                )

        models.UserSiteMapping.objects.bulk_create(user_site_mapping_objects)
        user_profile.save()
        return user_profile

    def check_if_email_already_active(
        self, email: str, is_active=True
    ) -> bool:
        """
        To check if the new email address already exists for another active user
        Params:
            email: New email address
        Returns:
            bool: True if the new email address already exists
        """
        return models.User.objects.filter(
            email=email, is_active=is_active
        ).exists()

    def check_if_email_already_exists(self, email: str) -> bool:
        """
        To check if the email address already exists among all records.
        Params:
            email: The email address to check
        Returns:
            bool: True if the email address already exists among inactive records
        """
        return models.User.objects.filter(email=email).exists()

    def get_existing_user(self, email: str) -> models.User:
        """
        To retrieve an existing user record with email
        Params:
            email: email to retrieve existing user
        Returns:
            user: user record
        """
        return models.User.objects.select_related("userprofiledetails").get(
            email=email
        )

    def user_invite_with_existing_user(
        self,
        admin_user: models.User,
        existing_user: models.User,
        first_name: str,
        last_name: str,
        site_list: list,
        user_type_id: int,
    ) -> models.UserProfileDetails:
        """
        To update the existing user profile for user invite
        Params:
            admin_user: admin who invited the user
            existing_user: existing user profile for the given email
            first_name: first name of the user
            last_name: last name of the user
            site_list: list of site assigned to the user by admin
            user_type_id: type of user profile
        Returns:
            user_profile_details: updated user profile details object for the given user
        """
        existing_user_profile = existing_user.userprofiledetails

        existing_user.first_name = first_name
        existing_user.last_name = last_name
        password = CommonController().generate_password()
        if existing_user:
            existing_user.set_password(password)
            existing_user.save()
        existing_user_profile.user_type_id = user_type_id
        existing_user_profile.is_active = False
        try:
            invite_user_object = models.InviteUser.objects.get(
                invited_user=existing_user
            )
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invite for given user does not exist",
                    "validation_error_field": "email",
                },
                code="validation_error",
            )
        invite_user_object.delete()

        models.InviteUser.objects.create(
            user=admin_user, invited_user=existing_user
        )

        user_site_mapping_objects = models.UserSiteMapping.objects.filter(
            user=existing_user
        )
        user_site_mapping_objects.delete()

        user_site_mapping_objects = []
        if site_list:
            for site in site_list:
                user_site_mapping_objects.append(
                    models.UserSiteMapping(
                        user=existing_user,
                        site_id=site,
                        is_active=True,
                    )
                )

        models.UserSiteMapping.objects.bulk_create(user_site_mapping_objects)
        existing_user_profile.save()
        return existing_user_profile

    def create_and_send_invite_mail(
        self, user_profile: models.UserProfileDetails
    ):
        """
        To send invite mail to a user
        Params:
            user_profile: user profile details of the user
        Returns:
            None
        """
        current_datetime = datetime.datetime.utcnow()
        data = (
            str(user_profile.user_type.id)
            + "^^^"
            + str(user_profile.user.email)
            + "^^^"
            + current_datetime.strftime(constants.DATE_TIME_FORMAT)
        )
        token = encrypt_decrypt.encrypt(data)
        end_point = (
            "customer_link"
            if user_profile.user_type.id == constants.UserTypeNames.CUSTOMER
            else "staff_link"
        )
        invite_url = "%ssignUp/%s/?invite_token=%s" % (
            settings.FRONT_END_BASE_URL,
            end_point,
            token,
        )
        mail_controller = mailing.UserMailing()
        mail_controller.send_invite_email(
            user_profile=user_profile, invite_url=invite_url
        )
        common_controller = CommonController()
        common_controller.add_token_to_reset_token_log(
            user=user_profile.user, token=token
        )

    def check_signup_invite_token(
        self, token: str, token_datetime_str: str
    ) -> models.ResetTokenLog:
        """
        To check if the sign up invite is already used or time out expired.
        Params:
            token: token from the sign up invite.
            token_datetime_str: datetime of the token creation decrypted from token.
        Returns:
            reset_token_log: token log entry if the token is valid.
        """

        token_log = CommonController().check_token_expired(token=token)
        if token_log is None:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Expired sign up link.",
                    "validation_error_field": "token",
                    "validation_error_message": "Expired token",
                },
                code="validation_error",
            )

        is_token_timeout = CommonController().check_token_timeout_expired(
            token_datetime_str=token_datetime_str
        )
        if is_token_timeout:
            token_log.is_expired = True
            token_log.token = ""
            token_log.save()
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Expired sign up link.",
                    "validation_error_field": "token",
                    "validation_error_message": "Time Out Expired token",
                },
                code="validation_error",
            )
        return token_log

    def set_user_password(
        self,
        token: str,
        password: str,
        confirm_password: str,
        is_active=True,
    ) -> bool:
        """
        Creating password for brand admin or organization admin after getting the email from uconnect admin.
        Params:
            token: verification token from reset link,
            password: new password,
            confirm_password: confirm new password,
        Returns:
            result: boolean value to indicate result of the password reset operation
        """
        result, data = encrypt_decrypt.decrypt(token)
        if result:
            email, token_datetime_str = str(data).split("^^^")
            token_log = self.check_password_reset_token(
                token=token, token_datetime_str=token_datetime_str
            )

            if not str(password) == str(confirm_password):
                raise serializers.ValidationError(
                    {
                        "result": False,
                        "msg": "Confirm password does not match the new password.",
                    },
                    code="validation_error",
                )

            try:
                user = User.objects.get(email=email, is_active=is_active)
            except exceptions.ObjectDoesNotExist:
                raise serializers.ValidationError(
                    {
                        "result": False,
                        "msg": "Invalid User to change the password",
                    },
                    code="validation_error",
                )
            self.password_history_check(user=user, password=password)
            self.change_password(user=user, password=password)
            token_log.is_expired = True
            token_log.token = ""
            token_log.save()
        return result

    def change_password(
        self,
        user: models.User,
        password: str,
    ):
        """
        To change the user password. New password will be compared against last 50 passwords for repetition

        Params:
            user: user object to change password
            password: New password entered by the user
        """
        user.set_password(password)
        user.save()
        models.PasswordHistory.objects.create(
            user=user, password=user.password
        )

    def check_password_reset_token(
        self, token: str, token_datetime_str: str
    ) -> models.ResetTokenLog:
        """
        To check the validity of the password reset token.
        Params:
            token: token from the password reset request.
            token_datetime_str: datetime of token creation decrypted from the token.
        Returns:
            reset_token_log: token log entry if the token is valid.
        """

        token_log = CommonController().check_token_expired(token=token)
        if token_log is None:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid or expired password reset link. Please initiate the forgot password process again.",
                    "validation_error_field": "token",
                    "validation_error_message": "Expired Invalid token",
                },
                code="validation_error",
            )

        is_token_timeout = CommonController().check_token_timeout_expired(
            token_datetime_str=token_datetime_str
        )
        if is_token_timeout:
            token_log.is_expired = True
            token_log.token = ""
            token_log.save()
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid or expired password reset link. Please initiate the forgot password process again.",
                    "validation_error_field": "token",
                    "validation_error_message": "Time Out Expired token",
                },
                code="validation_error",
            )
        return token_log

    def password_history_check(self, user: models.User, password: str):
        """
        To check if the newly entered password has been used in the past 50 cycles by the user.

        Params:
            user: user object
            password: new password to check against password history
        """
        user_password_history = models.PasswordHistory.objects.filter(
            user=user
        ).order_by("-created_on")
        count = 0
        for old_password_object in user_password_history:
            if check_password(password, old_password_object.password):
                raise serializers.ValidationError(
                    {
                        "result": False,
                        "msg": "Please choose a password that you haven't used before.",
                    },
                    code="validation_error",
                )
            if count > 50:
                break

    def get_user_by_email_user_type(
        self, email: str, user_type_id: int, is_active=True
    ) -> models.UserProfileDetails:
        """
        To check if the user has been created and invited by admin with email from sign up invite token
        Params:
            email: email of the user retrieved from the sign up invite token
        Returns:
            user_profile: Instance of UserProfileDetails
        """
        try:
            return models.UserProfileDetails.objects.select_related(
                "user", "user_type"
            ).get(
                user__email=email,
                user_type__id=user_type_id,
            )
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid email",
                    "validation_error_field": "email",
                },
                code="validation_error",
            )

    def get_user_profile_by_id(
        self,
        user_id: int,
        email: str,
        token_log: models.ResetTokenLog,
        is_active=True,
    ) -> models.UserProfileDetails:
        """
        To retrieve a user with unverified email based on the given email address
        Params:
            user_id: id of the user
            email: The email address received from the verification mail
            token_log: The token for email verification
            is_active: boolean to filter against active users
        Returns:
            user_profile_details: User profile details object associated with the email address
        """
        try:
            return models.UserProfileDetails.objects.select_related(
                "user", "user_type"
            ).get(user__id=user_id, new_email=email, is_active=is_active)
        except exceptions.ObjectDoesNotExist:
            token_log.is_expired = True
            token_log.token = ""
            token_log.save()
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "The verification link has expired or is invalid. Please request a new verification link.",
                    "validation_error_field": "email",
                },
                code="validation_error",
            )

    def get_invited_user(
        self, invited_user: models.User, is_active=True
    ) -> models.InviteUser:
        """
        To retrieve the user invite information from database
        params:
            invited_user: Instance of User that was invited by the admin
            is_active: To check against active invite user records
        Returns:
            invited_user_record: Instance of InviteUser corresponding to the given invited user
        """
        try:
            return models.InviteUser.objects.get(
                invited_user=invited_user, is_active=True
            )
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "User invite does not exist",
                },
                code="validation_error",
            )

    def get_user_profile_by_user(
        self, user: models.User, is_active=True
    ) -> models.UserProfileDetails:
        """
        To retrieve the user profile information from database to check for user type on API requests.
        params:
            user: Instance of User that was invited by the admin
            is_active: To check against active user records
        Returns:
            user_profile: Instance of UserProfileDetails corresponding to the given user
        """
        try:
            return models.UserProfileDetails.objects.select_related(
                "user_type"
            ).get(user=user, is_active=is_active)
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "User profile does not exist",
                },
                code="validation_error",
            )

    def get_designations(
        self,
        is_active=True,
    ) -> models.DesignationMaster:
        """
        To retrieve a queryset of all the designations from the database
        Params:
            is_active: To check against active designation records
        Returns:
            designation_objects: Queryset of all the designation objects
        """
        return models.DesignationMaster.objects.filter(is_active=is_active)

    def get_companies_with_sites(
        self,
        is_active=True,
    ) -> models.Company:
        """
        To retrieve a queryset of company objects with prefetching the associated sites
        Params:
            is_active: To check against active company records
        Returns:
            company_objects: Queryset of all the company objects
        """
        return models.Company.objects.prefetch_related("site_set").filter(
            is_active=is_active
        )

    def get_companies(
        self,
        is_active=True,
    ) -> models.Company:
        """
        To retrieve a queryset of all the companies from the database
        Params:
            is_active: To check against active company records
        Returns:
            company_objects: Queryset of all the company objects
        """
        return models.Company.objects.filter(is_active=is_active)

    def get_companies_by_user(
        self,
        user: models.User,
        is_active=True,
    ) -> models.Company:
        """
        To retrieve a queryset of all the companies associated with the given user
        Params:
            user: User object
            is_active: To check against active company records
        Returns:
            company_objects: Queryset of company objects associated with the given user
        """
        return models.Company.objects.filter(
            site__usersitemapping__user=user,
            site__usersitemapping__is_active=is_active,
        ).distinct()

    def get_sites(
        self,
        is_active=True,
    ) -> models.Site:
        """
        To retrive a queryset of all the site objects from the database
        Params:
            is_active: To check against active site records
        Returns:
            site_objects: Queryset of all the site objects
        """
        return models.Site.objects.select_related("company").filter(
            is_active=is_active
        )

    def get_sites_by_company_ids(
        self,
        company_ids: list,
        is_active=True,
    ) -> models.Site:
        """
        To retrieve a queryset of site objects based on give list of company ids
        Params:
            company_ids: List of company ids
            is_active: To check against active site records
        Returns:
            site_objects: Queryset of filtered site objects
        """
        return models.Site.objects.select_related("company").filter(
            company__id__in=company_ids, is_active=is_active
        )

    def get_sites_by_user(
        self,
        user: models.User,
        is_active=True,
    ) -> models.Site:
        """
        To retrieve a queryset of site objects for a given user
        Params:
            user: Given user object
            is_active: To check against active site records
        Returns:
            site_objects: A queryset of filtered site objects
        """
        return models.Site.objects.select_related("company").filter(
            usersitemapping__user=user,
            usersitemapping__is_active=is_active,
        )

    def get_sites_by_user_and_company_ids(
        self,
        user: models.User,
        company_ids: list,
        is_active=True,
    ) -> models.Site:
        """
        To retrieve a queryset of site objects for a given user and company IDs
        Params:
            user: Given user object
            is_active: To check against active site records
        Returns:
            site_objects: A queryset of filtered site objects
        """
        return models.Site.objects.select_related("company").filter(
            usersitemapping__user=user,
            company__id__in=company_ids,
            usersitemapping__is_active=is_active,
        )

    def check_user_site_mapping(
        self, user: models.User, site: models.Site, is_active=True
    ):
        """
        To check if the given site is associated with the user
        Params:
            user: user object.
            site: site object for the given site
            is_active: To check against active records.
        Returns:
            None
        """
        try:
            models.UserSiteMapping.objects.get(
                user=user, site=site, is_active=is_active
            )
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid site id for the user",
                    "validation_error_field": "site_id",
                },
                code="validation_error",
            )

    def get_user_by_id(self, user_id: int, is_active=True) -> models.User:
        """
        To retrieve user object based on given user id
        Params:
            user_id: id of the user
            is_active: To check against active user records
        Returns:
            user_object: User object
        """
        try:
            return models.User.objects.get(id=user_id, is_active=is_active)
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid user id",
                    "validation_error_field": "user_id",
                },
                code="validation_error",
            )

    def get_user_with_user_profile_by_id(
        self, user_id: int, is_active=False
    ) -> models.User:
        """
        To retrieve user object with user profile on given user id for resend email
        Params:
            user_id: id of the user
            is_active: False to check only against inactive users
        Returns:
            user_object: user object
        """
        try:
            return models.User.objects.select_related(
                "userprofiledetails", "userprofiledetails__user_type"
            ).get(id=user_id, is_active=is_active)
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid user id",
                    "validation_error_field": "user_id",
                },
                code="validation_error",
            )

    def get_all_users(
        self,
        user_type_id: int,
    ) -> models.User:
        """
        To retrieve a queryset of all users for a given user type with prefetch on userprofiledetails, usersitemapping
        Params:
            user_type_id: id of given user type (staff, customer, admin)
        Returns:
            user_objects: Queryset of all the user objects
        """
        return (
            models.User.objects.filter(
                userprofiledetails__user_type_id=user_type_id,
            )
            .prefetch_related(
                Prefetch(
                    "userprofiledetails",
                    queryset=models.UserProfileDetails.objects.select_related(
                        "designation"
                    ),
                ),
                Prefetch(
                    "usersitemapping_set",
                    queryset=models.UserSiteMapping.objects.select_related(
                        "site__company"
                    ),
                ),
            )
            .annotate(
                is_user_signup_complete=Case(
                    When(
                        userprofiledetails__date_joined__isnull=True,
                        then=Value(False),
                    ),
                    default=Value(True),
                    output_field=django_models.BooleanField(),
                ),
            )
            .annotate(
                user_site_mapping_is_active=Coalesce(
                    "usersitemapping__is_active",
                    Case(
                        When(
                            userprofiledetails__is_disabled=True,
                            then=Value(False),
                        ),
                        default=Value(True),
                        output_field=django_models.BooleanField(),
                    ),
                    output_field=django_models.BooleanField(),
                ),
            )
            .values(
                user_id=F("id"),
                user_site_mapping_id=F("usersitemapping__id"),
                is_user_signup_complete=F("is_user_signup_complete"),
                user_first_name=F("first_name"),
                user_last_name=F("last_name"),
                user_email=F("email"),
                company_id=F("usersitemapping__site__company_id"),
                company_name=F("usersitemapping__site__company__name"),
                site_id=F("usersitemapping__site_id"),
                site_name=F("usersitemapping__site__name"),
                country_code=F("userprofiledetails__country_code"),
                mobile_number=F("userprofiledetails__mobile_number"),
                user_site_mapping_is_active=F("user_site_mapping_is_active"),
            )
            .order_by(
                "-userprofiledetails__updated_on",
                "-usersitemapping__updated_on",
            )
        )

    def convert_user_objects_to_list_for_csv(
        self, user_type_id: int, user_objects: models.User
    ) -> tuple:
        """
        To convert the user objects queryset into a list of tuples for CSV
        Params:
            user_type_id: id of given user type (staff, customer, admin)
            user_objects: Queryset of all the user objects
        Returns:
            has_non_blank_others_designation: boolean indicating whether the any retrieved user objects have other designation name
            user_objects: List of tuples queryset of user objects
        """
        has_non_blank_others_designation = user_objects.filter(
            userprofiledetails__others_designation_name__isnull=False,
            userprofiledetails__others_designation_name__gt="",
        ).exists()

        user_objects = user_objects.annotate(
            user_mobile_number=Concat(
                F("userprofiledetails__country_code"),
                Value(" "),
                F("userprofiledetails__mobile_number"),
                output_field=django_models.CharField(),
            ),
        )

        if user_type_id == constants.UserTypeNames.CUSTOMER:
            values_list_fields = [
                "first_name",
                "last_name",
                "email",
                "user_mobile_number",
                "usersitemapping__site__company__name",
                "usersitemapping__site__name",
                "userprofiledetails__designation__name",
            ]
            if has_non_blank_others_designation:
                values_list_fields.extend(
                    [
                        "userprofiledetails__others_designation_name",
                    ]
                )
            values_list_fields.extend(
                [
                    "userprofiledetails__site_address",
                    "userprofiledetails__date_joined",
                ]
            )

        else:
            values_list_fields = [
                "first_name",
                "last_name",
                "email",
                "user_mobile_number",
                "usersitemapping__site__company__name",
                "usersitemapping__site__name",
                "userprofiledetails__designation__name",
            ]
            if has_non_blank_others_designation:
                values_list_fields.extend(
                    [
                        "userprofiledetails__others_designation_name",
                    ]
                )
            values_list_fields.extend(
                [
                    "userprofiledetails__date_joined",
                ]
            )

        user_objects = user_objects.values_list(*values_list_fields)

        return (has_non_blank_others_designation, user_objects)

    def get_user_objects_by_search(
        self,
        user_objects: models.User,
        search_text: str,
    ) -> models.User:
        """
        To retrieve a queryset of user objects for a given search text
        Params:
            user_objects: Queryset of the user objects
            search_text: Text to search for
        Returns:
            user_objects: Queryset of filtered user objects based on the search text
        """

        try:
            first = search_text.split(" ")[0]
            last = search_text.split(" ")[1]
        except IndexError:
            first = search_text.split(" ")[0]
            last = ""

        return user_objects.filter(
            (Q(first_name__icontains=first) & Q(last_name__icontains=last))
            | Q(first_name__icontains=search_text)
            | Q(last_name__icontains=search_text)
            | Q(email__icontains=search_text)
            | Q(country_code__icontains=search_text)
            | Q(mobile_number__icontains=search_text)
            | Q(company_name__icontains=search_text)
            | Q(site_name__icontains=search_text)
            | Q(userprofiledetails__designation__name__icontains=search_text)
            | Q(userprofiledetails__site_address__icontains=search_text)
        ).order_by("-userprofiledetails__updated_on")

    def get_user_objects_by_company(
        self,
        user_objects: models.User,
        company_filter: list,
    ) -> models.User:
        """
        To retrieve a queryset of user objects based on the list of company ids filter
        Params:
            user_objects: Queryset of the user objects
            company_filter: List of company ids
        Returns:
            user_objects: Queryset of filtered user objects based on the list of company ids
        """
        return user_objects.filter(company_id__in=company_filter).order_by(
            "-userprofiledetails__updated_on"
        )

    def get_user_objects_by_site(
        self,
        user_objects: models.User,
        site_filter: list,
    ) -> models.User:
        """
        To retrieve a queryset of user objects based on the list of site ids filter
        Params:
            user_objects: Queryset of the user objects
            site_filter: List of site ids
        Returns:
            user_objects: Queryset of filtered user objects based on the list of site ids
        """
        return user_objects.filter(site_id__in=site_filter).order_by(
            "-userprofiledetails__updated_on"
        )

    def get_sort_field(
        self,
        sort_order: tuple,
    ) -> str:
        """
        To generate a sort configuration based on the sort selection
        Params:
            sort_order: Tuple of (sort_field, sort_order)
        Returns:
            sort_field: String representing the sort field along with order
        """
        return ("" if sort_order[1] == 1 else "-") + sort_order[0]

    def get_user_objects_first_name_sorted(
        self,
        user_objects: models.User,
        first_name_sort: tuple,
    ) -> models.User:
        """
        To sort the given user queryset based on first name and given sort order
        Params:
            user_objects: Queryset of the user objects
            first_name_sort: Tuple of (sort_field, sort_order)
        Returns:
            user_objects: sorted user queryset based on first name and given sort order
        """
        sort_field = self.get_sort_field(sort_order=first_name_sort)
        return user_objects.order_by(sort_field)

    def get_user_objects_last_name_sorted(
        self,
        user_objects: models.User,
        last_name_sort: tuple,
    ) -> models.User:
        """
        To sort the given user queryset based on last name and given sort order
        Params:
            user_objects: Queryset of the user objects
            last_name_sort: Tuple of (sort_field, sort_order)
        Returns:
            user_objects: sorted user queryset based on last name and given sort order
        """
        sort_field = self.get_sort_field(sort_order=last_name_sort)
        return user_objects.order_by(sort_field)

    def get_user_objects_company_sorted(
        self,
        user_objects: models.User,
        company_sort: tuple,
    ) -> models.User:
        """
        To sort the given user queryset based on company name and given sort order
        Params:
            user_objects: Queryset of the user objects
            company_sort: Tuple of (sort_field, sort_order)
        Returns:
            user_objects: sorted user queryset based on company name and given sort order
        """
        sort_field = self.get_sort_field(sort_order=company_sort)
        return user_objects.order_by(sort_field)

    def get_user_objects_site_sorted(
        self,
        user_objects: models.User,
        site_sort: tuple,
    ) -> models.User:
        """
        To sort the given user queryset based on site name and given sort order
        Params:
            user_objects: Queryset of the user objects
            site_sort: Tuple of (sort_field, sort_order)
        Returns:
            user_objects: sorted user queryset based on site name and given sort order
        """
        sorted_field = self.get_sort_field(sort_order=site_sort)
        return user_objects.order_by(sorted_field)

    def get_paginated_response(
        self,
        queryset: django_models.QuerySet,
        offset: int,
        limit: int,
    ) -> typing.Tuple[dict, bool]:
        """
        Custom pagination method for user queryset
        Params:
            queryset: Queryset of the user objects
            offset: Pagination offset
            limit: Pagination limit
        Returns:
            paginated_response: Dictionary of paginated response
            next_page_exists: Boolean to check if next page exists
        """
        try:
            offset = int(offset)
            previous_limit = int(limit)
        except ValueError:
            raise serializers.ValidationError(
                {"result": False, "msg": "limit or offset should be numbers"},
                code="validation_error",
            )

        limit = offset + previous_limit
        queryset_data = queryset[int(offset) : limit]

        if len(queryset) > limit:
            next_link = True
            user_data = queryset_data
        else:
            next_link = False
            user_data = queryset_data
        return user_data, next_link

    def get_user_with_profile_and_site_by_id(
        self, user_id: int
    ) -> models.User:
        """
        To retrieve a user object based on its id with prefetch on userprofiledetails and usersitemapping
        Params:
            user_id: User id
            is_active: To check against active users
        Returns:
            user: User object
        """
        try:
            return models.User.objects.prefetch_related(
                Prefetch(
                    "userprofiledetails",
                    queryset=models.UserProfileDetails.objects.select_related(
                        "designation"
                    ),
                ),
                Prefetch(
                    "usersitemapping_set",
                    queryset=models.UserSiteMapping.objects.select_related(
                        "site__company"
                    ),
                ),
            ).get(id=user_id)
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid user id",
                    "validation_error_field": "user_id",
                },
                code="validation_error",
            )

    def get_designation_by_id(
        self, designation_id: int, is_active=True
    ) -> models.DesignationMaster:
        """
        To retrieve a designation object based on its id
        Params:
            designation_id: Designation id provided by the user
            is_active: To check against active designations
        Returns:
            designation: Designation object
        """
        try:
            return models.DesignationMaster.objects.get(
                id=designation_id, is_active=is_active
            )
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid designation id",
                    "validation_error_field": "designation_id",
                },
                code="validation_error",
            )

    def get_user_profile_by_user_id(
        self,
        user_id: int,
    ) -> models.UserProfileDetails:
        """
        To get the user profile object by user id
        Params:
            user_id: User id chosen by the admin user
        Returns:
            user_profile: User profile object
        """
        try:
            return models.UserProfileDetails.objects.select_related(
                "user", "site_preference"
            ).get(user_id=user_id)
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid user id",
                    "validation_error_field": "user_id",
                },
                code="validation_error",
            )

    def get_user_site_mapping_by_id(
        self, user_site_mapping_id: models.UserSiteMapping
    ) -> models.UserSiteMapping:
        """
        To get the user_site_mapping_object based on the given user_site_mapping_id
        Params:
            user_site_mapping_id: User site mapping id
        Returns:
            user_site_mapping: User site mapping object
        """
        try:
            return models.UserSiteMapping.objects.get(id=user_site_mapping_id)
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Invalid user site mapping id",
                    "validation_error_field": "user_site_mapping_id",
                },
                code="validation_error",
            )

    def get_user_site_mappings_by_user(
        self, user: models.User, is_active=True
    ) -> models.UserSiteMapping:
        """
        To the queryset of active user_site_mapping objects for a given user
        Params:
            user: User object
            is_active: To check against active users
        Returns:
            user_site_mappings: Queryset of user_site_mapping objects
        """
        return models.UserSiteMapping.objects.select_related("site").filter(
            user_id=user, is_active=is_active
        )

    def update_user_site_mappings(
        self,
        user: models.User,
        usersitemappings: models.UserSiteMapping,
        site_list: list,
    ) -> models.User:
        """
        To update the user site mapping records based on the user given site list
        Params:
            user: User object
            usersitemappings: queryset of current user site mapping objects
            site_list: List of user given site ids
        """
        existing_sites_list = []
        delete_user_site_mappings = usersitemappings
        for usersitemapping in usersitemappings:
            if usersitemapping.site.id in site_list:
                delete_user_site_mappings = delete_user_site_mappings.exclude(
                    id=usersitemapping.id
                )
                existing_sites_list.append(usersitemapping.site.id)
        difference_list = list(set(site_list) - set(existing_sites_list))
        new_usersitemappings_list = []
        for site_id in difference_list:
            new_usersitemappings_list.append(
                models.UserSiteMapping(user=user, site_id=site_id)
            )
        delete_user_site_mappings.delete()
        models.UserSiteMapping.objects.bulk_create(new_usersitemappings_list)
        if difference_list:
            user.userprofiledetails.is_disabled = False
        return user

    def get_user_profile_with_site_by_user(
        self, user: models.User, is_active=True
    ) -> models.UserProfileDetails:
        """
        To retrieve the user profile information along with site, company preference from database to check for user type on API requests.
        Params:
            user: Instance of User that was invited by the admin
            is_active: To check against active user records
        Returns:
            user_profile: Instance of UserProfileDetails corresponding to the given user
        """
        try:
            return models.UserProfileDetails.objects.select_related(
                "user_type", "site_preference", "site_preference__company"
            ).get(user=user, is_active=is_active)
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "User profile does not exist.",
                },
                code="validation_error",
            )

    def get_site_by_id(
        self,
        site_id: int,
        is_active=True,
    ) -> models.Site:
        """
        To site object based on site id
        Params:
            site_id: id of the selected site
            is_active: To check against active site records
        Returns:
            site: Site object
        """
        try:
            return models.Site.objects.select_related("company").get(
                id=site_id, is_active=is_active
            )
        except exceptions.ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Site does not exist for the given site id.",
                    "validation_error_field": "site_id",
                },
                code="validation_error",
            )
