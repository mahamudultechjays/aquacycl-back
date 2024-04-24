import datetime

import boto3
import botocore
from django.conf import settings
from django.template.loader import render_to_string

from aquacycl_project import constants
from tj_packages import encrypt_decrypt


def send(username: str, email_id: str, verification_url: str):
    SENDER = settings.BASE_FROM_EMAIL
    RECIPIENT = email_id
    SUBJECT = f"Please verify your email address | Aquacycl {settings.ENV}"
    BODY_TEXT = "Amazon SES"
    context = {
        "email_id": email_id,
        "username": username,
        "verification_url": verification_url,
    }
    BODY_HTML = render_to_string("send_verification_mail.html", context)
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
        raise botocore.exceptions.ClientError(
            {
                "result": False,
                "msg": "Failed to send verification email. Please try again later.",
            },
            code="client_error",
        )

    else:
        print("Email sent! Message ID:"),
        print(response["MessageId"])


def send_mail(
    user_id: int,
    email: str,
    first_name: str,
    last_name: str,
) -> str:
    current_datetime = datetime.datetime.utcnow()
    data = (
        str(user_id)
        + "^^^"
        + str(email)
        + "^^^"
        + current_datetime.strftime(constants.DATE_TIME_FORMAT)
    )
    token = encrypt_decrypt.encrypt(data=data)
    username = f"{first_name} {last_name}".strip()

    verification_url = (
        f"{settings.FRONT_END_BASE_URL}verifyLink/?verifytoken={token}"  # noqa
    )
    send(
        username=username,
        email_id=email,
        verification_url=verification_url,
    )
    return token
