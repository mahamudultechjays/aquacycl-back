import json

from django.contrib import auth
from django.core import exceptions

from tj_packages import encrypt_decrypt

User = auth.get_user_model()


def verify_email(token: str):
    result, data = encrypt_decrypt.decrypt(token=token)
    if result is True:
        data = json.loads(data)
        email = data.get("email", "")
        try:
            user = User.objects.select_related("userprofiledetails").get(
                email=email
            )
        except exceptions.ObjectDoesNotExist:
            return "Invalid Email Address"

        if (not user.userprofiledetails.is_email_verified) or (
            user.userprofiledetails.is_email_verified
            and user.is_active is False
        ):
            user.userprofiledetails.is_email_verified = True
            user.is_active = True
            user.userprofiledetails.save()
            user.save()
            return user, email, "Your email address has been verified"
        else:
            return None, email, "Your email address has been already verified"
