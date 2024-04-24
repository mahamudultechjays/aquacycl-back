import boto3
import botocore
from django.contrib import auth
from django.template.loader import render_to_string

from aquacycl_project import settings
from users import models

User = auth.get_user_model()


class UserMailing:
    def send_invite_email(
        self,
        user_profile: models.UserProfileDetails,
        invite_url: str,
    ):
        """
        Send email to user to invite them to join the platform
        Params:
            user_profile: UserProfileDetails object associated with the invited user
            invite_url: URL for the signup page for the invited user
        """
        SENDER = settings.BASE_FROM_EMAIL
        RECIPIENT = user_profile.user.email
        SUBJECT = f"Sign up Invite | Aquacycl {settings.ENV}"
        BODY_TEXT = "Amazon SES"
        context = {
            "email_id": user_profile.user.email,
            "username": user_profile.user.username,
            "first_name": user_profile.user.first_name,
            "last_name": user_profile.user.last_name,
            "invite_url": invite_url,
        }
        BODY_HTML = render_to_string(
            "send_invite_to_staff_and_customer.html", context
        )
        CHARSET = "UTF-8"
        client = boto3.client(
            "ses",
            region_name=settings.SES_AWS_REGION,
            aws_access_key_id=settings.SES_ACCESS_KEY_ID,
            aws_secret_access_key=settings.SES_SECRET_ACCESS_KEY,
        )
        try:
            response = client.send_email(
                Destination={
                    "ToAddresses": [
                        RECIPIENT,
                    ],
                },
                Message={
                    "Body": {
                        "Html": {
                            "Charset": CHARSET,
                            "Data": BODY_HTML,
                        },
                        "Text": {
                            "Charset": CHARSET,
                            "Data": BODY_TEXT,
                        },
                    },
                    "Subject": {
                        "Charset": CHARSET,
                        "Data": SUBJECT,
                    },
                },
                Source=SENDER,
            )
        except botocore.exceptions.ClientError as e:
            print(e.response["Error"]["Message"])
        else:
            print("Email sent! Message ID:"),
            print(response["MessageId"])
