from rest_framework.views import exception_handler

from tj_packages import log


@log.log_error()
def custom_exception_handler(exc, context):

    """Call REST framework's default exception handler first,
    to get the standard error response."""
    response = exception_handler(exc, context)

    """if response == None it is not Rest Framework Error,
    unhandled errors raised and logged in error file."""
    if response is None:
        raise

    res = response.data.get("result", "")
    """Now add the HTTP status code to the response."""
    if res:
        response.data["result"] = False
    return response
