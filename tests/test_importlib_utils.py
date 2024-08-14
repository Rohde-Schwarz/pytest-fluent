import logging
import types

import pytest
from pytest_fluent.importlib_utils import (
    extract_function_from_module_string,
    load_module_from_path,
)


def test_load_module_from_path(record_formatter_file):
    module = load_module_from_path(record_formatter_file)
    assert isinstance(module, types.ModuleType)


def test_load_module_from_path_error():
    with pytest.raises(ModuleNotFoundError, match="Could not load module abc"):
        load_module_from_path("abc")


def test_extract_function_from_module_string_path(record_formatter_file):
    record_formatter = extract_function_from_module_string(
        "RecordFormatter", file_path=record_formatter_file
    )
    assert issubclass(record_formatter, logging.Formatter)


def test_extract_function_from_module_string_module():
    record_formatter = extract_function_from_module_string(
        "Formatter", module="logging"
    )
    assert issubclass(record_formatter, logging.Formatter)


def test_extract_function_from_module_string_no_module_or_path():
    with pytest.raises(ValueError, match="Neither module nor file_path was set."):
        extract_function_from_module_string("Formatter")


def test_extract_function_from_module_string_no_formatter_type():
    with pytest.raises(
        ValueError,
        match="Provided record formatter is not derived from logging.Formatter",
    ):
        extract_function_from_module_string("Filterer", module="logging")


def test_extract_function_from_module_string_import_error():
    with pytest.raises(
        ImportError,
        match="Could not find abc in logging",
    ):
        extract_function_from_module_string("abc", module="logging")
