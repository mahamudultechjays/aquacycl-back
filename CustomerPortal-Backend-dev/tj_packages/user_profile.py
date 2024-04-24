import datetime

from django.contrib import auth
from django.db import models as django_models

from tj_packages import image_optimization
from users import models

User = auth.get_user_model()


def update_user_and_profile_data(
    user_profile_data: django_models.QuerySet,
    first_name: str,
    last_name: str,
    password: str,
    country_code: str,
    mobile_number: str,
    user_type_object: models.UserType,
    designation_object: models.DesignationMaster,
    others_designation_name: str,
    site_address: str,
    source: str,
    is_active: bool,
    is_email_verfied=True,
) -> models.UserProfileDetails:
    """
    To update record in user profile table incase of an existing user

    Params:
        user_profile_data: the existing user profile associated with the user
        first_name: first name of the user
        last_name: last name of the user
        password: password provided by the user
        country_code: telephone country code detail of the user
        mobile_number: mobile number of the user
        user_type_object: user_type detail of the user
        designation_object: designation detail of the user
        others_designation_name: the user provided designation detail incase of "others" option
        site_address: user provided site address incase of customer, empty string incase of staff and admin
        source: the platform used by the user for sign up
        is_active: to set the user record as active

    Returns:
        user_profile_data: the updated user profile object
    """
    user_profile_data.user.first_name = first_name
    user_profile_data.user.last_name = last_name
    user_profile_data.user.set_password(password)
    user_profile_data.user.is_active = is_active
    user_profile_data.user.save()

    user_profile_data.source = str(source).lower().strip()
    user_profile_data.country_code = country_code
    user_profile_data.mobile_number = mobile_number
    user_profile_data.user_type = user_type_object
    user_profile_data.designation = designation_object
    user_profile_data.others_designation_name = others_designation_name
    user_profile_data.site_address = site_address
    user_profile_data.is_active = is_active
    user_profile_data.is_email_verified = is_email_verfied
    user_profile_data.date_joined = datetime.datetime.utcnow()
    user_profile_data.save()
    return user_profile_data


def update_profile_pic(
    image: object, user: User, user_profile: models.UserProfileDetails
) -> models.UserProfileDetails:
    try:
        ext = str(image.name).split(".")[-1]
        image_name = f"profile{user.id}.{ext}"
        thumb_size = (128, 128)
        medium_size = (356, 356)
        thumb_image = image_optimization.get_optimized_image(
            image, image_name, 80, ext, thumb_size
        )
        medium_image = image_optimization.get_optimized_image(
            image, image_name, 70, ext, medium_size
        )
        normal_image = image_optimization.get_optimized_image(
            image, image_name, 70, ext
        )
        user_profile.thumbnail_profile_pic = thumb_image
        user_profile.medium_profile_pic = medium_image
        user_profile.profile_pic = normal_image
        user_profile.save()
    except:  # noqa
        pass
    return user_profile
