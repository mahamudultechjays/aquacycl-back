from cryptography import fernet
from rest_framework import serializers

from aquacycl_project import constants


def encrypt(data):
    # key = Fernet.generate_key()
    f = fernet.Fernet(str(constants.ENCRYPTION_PASSWORD).encode())
    final_data = str(
        str(data) + "<><><>" + str(constants.ENCRYPTION_SALT)
    ).encode()
    token = f.encrypt(final_data)
    return token.decode()


def decrypt(token):
    try:
        f = fernet.Fernet(str(constants.ENCRYPTION_PASSWORD).encode())
        data = f.decrypt(str(token).encode())
        decoded_data = data.decode()
        actual_data, salt = decoded_data.split("<><><>")
        if str(salt) == (constants.ENCRYPTION_SALT):
            return True, actual_data
        else:
            return False, actual_data
    except Exception:
        raise serializers.ValidationError(
            {
                "result": False,
                "msg": "Invalid Token",
            },
            code="validation_error",
        )
