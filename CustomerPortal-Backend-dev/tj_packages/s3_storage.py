from django.conf import settings
from storages.backends import s3boto3

if settings.ENV == "DEV" or settings.ENV == "STG" or settings.ENV == "PRD":

    class StaticStorage(s3boto3.S3Boto3Storage):
        location = settings.AWS_STATIC_LOCATION
        default_acl = "public-read"


class PublicMediaStorage(s3boto3.S3Boto3Storage):
    location = settings.AWS_PUBLIC_MEDIA_LOCATION
    default_acl = "public-read"
    file_overwrite = True


class PrivateMediaStorage(s3boto3.S3Boto3Storage):
    location = settings.AWS_PRIVATE_MEDIA_LOCATION
    default_acl = "private"
    file_overwrite = True
    custom_domain = False
