# Encryption Decryption Key
ENCRYPTION_PASSWORD = "e0hNthUefdCBQ1mQ6rT6xLLrPDBQdxUCumjvYUd6S2w="
ENCRYPTION_SALT = "ZXCVBNMJYTTTTTTTSALT"

# AWS CREDENTIALS
AWS_REGION = "us-west-2"

AWS_S3_REGION_NAME = "us-west-2"

# S3 Bucket Details
AWS_STORAGE_BUCKET_NAME = {
    "LOCAL": "dev-aquacycl-s3-bucket",
    "DEV": "dev-aquacycl-s3-bucket",
    "QA": "",
    "STG": "",
    "PROD": "",
}

# Cloudfront Details
AWS_S3_CUSTOM_DOMAIN = {
    "LOCAL": "d2zzzeyzow1636.cloudfront.net",
    "DEV": "d2zzzeyzow1636.cloudfront.net",
    "QA": "",
    "STG": "",
    "PROD": "",
}

# AWS S3 CONFIGURATIONS
AWS_PUBLIC_MEDIA_LOCATION = "media/public"
DEFAULT_FILE_STORAGE = "tj_packages.s3_storage.PublicMediaStorage"

AWS_PRIVATE_MEDIA_LOCATION = "media/private"
PRIVATE_FILE_STORAGE = "tj_packages.s3_storage.PrivateMediaStorage"

AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_EXPIRE = "36000"

AWS_PUBLIC_URL = {
    "LOCAL": "https://%s/%s/"
    % (AWS_S3_CUSTOM_DOMAIN["LOCAL"], AWS_PUBLIC_MEDIA_LOCATION),
    "DEV": "https://%s/%s/"
    % (AWS_S3_CUSTOM_DOMAIN["DEV"], AWS_PUBLIC_MEDIA_LOCATION),
    "QA": "https://%s/%s/"
    % (AWS_S3_CUSTOM_DOMAIN["QA"], AWS_PUBLIC_MEDIA_LOCATION),
    "STG": "https://%s/%s/"
    % (AWS_S3_CUSTOM_DOMAIN["STG"], AWS_PUBLIC_MEDIA_LOCATION),
    "PROD": "https://%s/%s/"
    % (AWS_S3_CUSTOM_DOMAIN["PROD"], AWS_PUBLIC_MEDIA_LOCATION),
}

AWS_STATIC_LOCATION = "static"
STATIC_URL = {
    "LOCAL": "/static/",
    "DEV": "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_STATIC_LOCATION),
    "QA": "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_STATIC_LOCATION),
    "STG": "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_STATIC_LOCATION),
    "PROD": "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_STATIC_LOCATION),
}


# BASE URL Details
BASE_URL = {
    "LOCAL": "http://127.0.0.1:8000/",
    "DEV": "https://dev-customerportal-api.aquacycl.com/",
    "QA": "",
    "STG": "",
    "PROD": "",
}

# FRONT END BASE URL
FRONT_END_BASE_URL = {
    "LOCAL": "http://localhost:3000/",
    "DEV": "https://dev-customerportal.aquacycl.com/",
    "QA": "",
    "STG": "",
    "PROD": "",
}


LOG_PATH = ">> /var/log/aquacycl/logs.log"

IMAGE_EXT = ["jpg", "jpeg", "png", "gif", "bmp", "svg", "blob", "webp"]


DATE_FORMAT = "%m-%d-%Y"
TIME_FORMAT = "%H:%M:%S"
DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

SORT_ORDER_OPTIONS = {
    "ascending": 1,
    "no_sort": 0,
    "descending": 2,
}


BASE_FROM_EMAIL = {
    "LOCAL": "info@aquacycl.com",
    "DEV": "info@aquacycl.com",
}


class UserTypeNames:
    ADMIN = 1
    STAFF = 2
    CUSTOMER = 3


class DesignationNames:
    MANAGER = 1
    SUPERVISOR = 2
    OPERATOR = 3
    TECHNICIAN = 4
    SAFETY_OFFICER = 5
    ENGINEER = 6
    OTHERS = 7


class Manifest:
    GITHUB_DOMAIN = "github.com"
    OWNER = "AquaCycl"
    REPO_NAME_HEADER = "siteDeployment"
    SUBTOPIC_BIT_NUMBER = "subtopicBitNumber"
    SUBTOPIC_REPORTED_ON = "subtopicReportedOn"
