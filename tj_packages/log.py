import functools
import logging
import sys
import traceback

from rest_framework import response, status


def _generate_log(path):
    """Create a logger and set the level."""
    logger = logging.getLogger("fay")
    logger.setLevel(logging.ERROR)
    """Create file handler, log format and add the format to file handler"""
    file_handler = logging.FileHandler(path)
    log_format = "%(levelname)s %(asctime)s %(message)s"
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(file_handler)
    return logger


def log_error(path="log/errors.log"):
    def error_log(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error_msg = repr(traceback.format_tb(exc_traceback))
                logger = _generate_log(path)
                logger.error(error_msg)
                return response.Response(
                    {
                        "result": False,
                        "msg": "Internal Server Error Try again later",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return wrapper

    return error_log
