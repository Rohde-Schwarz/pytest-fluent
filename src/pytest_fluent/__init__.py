"""pytest-fluent-logging."""
import sys

if sys.version_info >= (3, 8):
    from importlib.metadata import PackageNotFoundError, version
else:
    from importlib_metadata import PackageNotFoundError  # type: ignore
    from importlib_metadata import version  # type: ignore

__version__ = "unknown"
try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    pass


from .additional_information import (
    additional_session_information_callback,
    additional_test_information_callback,
)
from .plugin import get_session_uid, get_test_uid

__all__ = [
    "additional_session_information_callback",
    "additional_test_information_callback",
    "get_session_uid",
    "get_test_uid",
]
