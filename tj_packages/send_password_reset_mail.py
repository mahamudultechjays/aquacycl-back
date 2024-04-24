import boto3
import botocore
from django.template.loader import render_to_string

# from django.conf import settings
from aquacycl_project import settings


def send_mail(email_id: str, username: str, verification_url: str):
    SENDER = settings.BASE_FROM_EMAIL
    RECIPIENT = email_id
    SUBJECT = f"Password Reset | Aquacycl {settings.ENV}"
    BODY_TEXT = "Amazon SES"
    context = {
        "verification_url": verification_url,
        "username": username,
    }
    print(verification_url, "url-----")
    BODY_HTML = render_to_string("send_reset_password_mail.html", context)
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
