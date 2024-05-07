import logging
from unittest.mock import MagicMock, patch

from pytest_fluent.content_patcher import ContentPatcher
from pytest_fluent.plugin import (
    RecordFormatter,
    add_handler,
    get_formatter,
    overflow_handler,
)


def test_get_formatter_default():
    patcher = MagicMock()
    patcher.user_settings = {}
    formatter = get_formatter(patcher)
    assert isinstance(formatter, RecordFormatter)


def test_get_formatter_custom(record_formatter_file):
    patcher = MagicMock(spec=ContentPatcher)
    patcher.user_settings = {
        "logging": {
            "recordFormatter": {
                "className": "RecordFormatter",
                "filePath": str(record_formatter_file),
            }
        }
    }
    formatter = get_formatter(patcher)
    assert isinstance(formatter, logging.Formatter)


@patch("pytest_fluent.plugin.FluentHandler")
def test_add_handler(mock_fluent_handler: MagicMock):
    logger = MagicMock(spec=logging.Logger)
    patcher = MagicMock(spec=ContentPatcher)
    patcher.user_settings = {}
    add_handler("abc", 8080, "test.tag", logger, patcher)
    mock_fluent_handler.assert_called_once_with(
        "test.tag", host="abc", port=8080, buffer_overflow_handler=overflow_handler
    )
    mock_fluent_handler.return_value.setFormatter.assert_called_once()
    logger.addHandler.assert_called_once_with(mock_fluent_handler.return_value)
