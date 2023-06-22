"""pytest-fluent-logging."""

from importlib.metadata import PackageNotFoundError, version

from .additional_information import (
    additional_information_callback,
    additional_session_information_callback,
    additional_test_information_callback,
)
from .plugin import get_session_uid, get_test_uid

__version__ = "unknown"
try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    pass


__all__ = [
    "additional_session_information_callback",
    "additional_test_information_callback",
    "additional_information_callback",
    "get_session_uid",
    "get_test_uid",
]
