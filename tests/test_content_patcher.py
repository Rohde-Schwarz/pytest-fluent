"""Tests for ContentPatcher."""
# pylint: disable=W0212, C0116, W0621
import argparse
import os
import typing
import uuid

import pytest

from pytest_fluent.content_patcher import ContentPatcher, _ContentType
from pytest_fluent.plugin import FluentLoggerRuntime

UNIQUE_IDENTIFIER = str(uuid.uuid4())


@pytest.fixture
def stage_names() -> typing.List[str]:
    names = [
        method for method in dir(FluentLoggerRuntime) if method.startswith("pytest_")
    ]
    names.append("logging")
    return names


@pytest.fixture
def user_settings() -> dict:
    return {
        "all": {
            "tag": "run",
            "label": "pytest",
            "replace": {"status": "state", "sessionId": "id"},
        },
        "pytest_sessionstart": {
            "tag": "run",
            "label": "test",
            "add": {"start_info": "Pytest started"},
        },
        "pytest_sessionfinish": {
            "tag": "result",
            "label": "test",
            "add": {"stop_info": "Pytest finished"},
        },
        "pytest_runtest_logstart": {
            "tag": "run",
            "label": "testcase",
            "add": {"start_info": "Testcase started"},
        },
        "pytest_runtest_logreport": {
            "tag": "result",
            "label": "testcase",
            "add": {"stop_info": "Testcase finished"},
        },
    }


@pytest.fixture
def user_settings_patched() -> dict:
    return {
        "pytest_runtest_call": {
            "tag": "run",
            "label": "pytest",
            "replace": {"status": "state", "sessionId": "id"},
        },
        "pytest_runtest_logfinish": {
            "tag": "run",
            "label": "pytest",
            "replace": {"status": "state", "sessionId": "id"},
        },
        "pytest_runtest_logreport": {
            "tag": "result",
            "label": "testcase",
            "replace": {"status": "state", "sessionId": "id"},
            "add": {"stop_info": "Testcase finished"},
        },
        "pytest_runtest_logstart": {
            "tag": "run",
            "label": "testcase",
            "replace": {"status": "state", "sessionId": "id"},
            "add": {"start_info": "Testcase started"},
        },
        "pytest_runtest_makereport": {
            "tag": "run",
            "label": "pytest",
            "replace": {"status": "state", "sessionId": "id"},
        },
        "pytest_runtest_setup": {
            "tag": "run",
            "label": "pytest",
            "replace": {"status": "state", "sessionId": "id"},
        },
        "pytest_runtest_teardown": {
            "tag": "run",
            "label": "pytest",
            "replace": {"status": "state", "sessionId": "id"},
        },
        "pytest_sessionfinish": {
            "tag": "result",
            "label": "test",
            "replace": {"status": "state", "sessionId": "id"},
            "add": {"stop_info": "Pytest finished"},
        },
        "pytest_sessionstart": {
            "tag": "run",
            "label": "test",
            "replace": {"status": "state", "sessionId": "id"},
            "add": {"start_info": "Pytest started"},
        },
        "logging": {
            "tag": "run",
            "label": "pytest",
            "replace": {"status": "state", "sessionId": "id"},
        },
    }


@pytest.fixture
def stage_content() -> dict:
    return {}


@pytest.fixture
def stage_content_patched() -> dict:
    return {}


@pytest.fixture
def namespace() -> argparse.Namespace:
    return argparse.Namespace(**{"fluentd-tag": "pytest"})


def test_is_reference_string():
    assert ContentPatcher._is_reference_string("${USE_ENV}") == _ContentType.ENV
    assert ContentPatcher._is_reference_string("<tag>") == _ContentType.ARGS


def test_get_env_content__no_env_string():
    assert ContentPatcher._get_env_content("test") == ""


def test_get_env_content__env_string():
    result = "test"
    os.environ["USE_ENV"] = result
    assert ContentPatcher._get_env_content("$USE_ENV") == result
    assert ContentPatcher._get_env_content("${USE_ENV}") == result


def test_get_env_content__env_string_no_content():
    assert ContentPatcher._get_env_content("$USE_ENV") == ""


def test_get_args_content__retrieve_content(stage_content, namespace, stage_names):
    patcher = ContentPatcher(
        user_settings=stage_content, args_settings=namespace, stage_names=stage_names
    )
    assert patcher._get_args_content("<fluentd-tag>") == "pytest"


def test_get_args_content__retrieve_no_content(stage_content, namespace, stage_names):
    patcher = ContentPatcher(
        user_settings=stage_content, args_settings=namespace, stage_names=stage_names
    )
    assert patcher._get_args_content("<fluentd-label>") == ""


def test_stage_settings(user_settings, user_settings_patched, stage_names):
    patched = ContentPatcher._stage_settings(user_settings, stage_names)
    assert patched == user_settings_patched


@pytest.mark.parametrize(
    "to_patch,expected,stage",
    [
        (
            {
                "status": "start",
                "stage": "session",
                "sessionId": UNIQUE_IDENTIFIER,
            },
            {
                "tag": "run",
                "label": "test",
                "state": "start",
                "stage": "session",
                "id": UNIQUE_IDENTIFIER,
                "start_info": "Pytest started",
            },
            "pytest_sessionstart",
        ),
        (
            {
                "status": "finish",
                "stage": "session",
                "sessionId": UNIQUE_IDENTIFIER,
            },
            {
                "tag": "result",
                "label": "test",
                "state": "finish",
                "stage": "session",
                "id": UNIQUE_IDENTIFIER,
                "stop_info": "Pytest finished",
            },
            "pytest_sessionfinish",
        ),
        (
            {
                "status": "start",
                "stage": "testcase",
                "sessionId": UNIQUE_IDENTIFIER,
                "testId": UNIQUE_IDENTIFIER,
                "name": "testcase",
            },
            {
                "tag": "run",
                "label": "testcase",
                "state": "start",
                "stage": "testcase",
                "id": UNIQUE_IDENTIFIER,
                "testId": UNIQUE_IDENTIFIER,
                "name": "testcase",
                "start_info": "Testcase started",
            },
            "pytest_runtest_logstart",
        ),
        (
            {
                "status": "finish",
                "stage": "testcase",
                "sessionId": UNIQUE_IDENTIFIER,
                "testId": UNIQUE_IDENTIFIER,
                "name": "testcase",
            },
            {
                "tag": "result",
                "label": "testcase",
                "state": "finish",
                "stage": "testcase",
                "id": UNIQUE_IDENTIFIER,
                "testId": UNIQUE_IDENTIFIER,
                "name": "testcase",
                "stop_info": "Testcase finished",
            },
            "pytest_runtest_logreport",
        ),
    ],
)
def test_patch_content(to_patch, expected, stage, user_settings_patched):
    patched = ContentPatcher._patch_stage_content(
        to_patch, user_settings_patched[stage]
    )
    assert patched == expected


def test_get_tag_and_label(
    user_settings, namespace, stage_names, user_settings_patched
):
    stage = "pytest_runtest_logstart"
    patcher = ContentPatcher(
        user_settings=user_settings, args_settings=namespace, stage_names=stage_names
    )
    assert patcher.get_tag_and_label(stage) == (
        user_settings_patched[stage]["tag"],
        user_settings_patched[stage]["label"],
    )

    def pytest_runtest_logstart():
        return patcher.get_tag_and_label()

    assert pytest_runtest_logstart() == (
        user_settings_patched[stage]["tag"],
        user_settings_patched[stage]["label"],
    )
