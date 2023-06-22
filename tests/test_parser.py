import argparse
import os

import pytest

from pytest_fluent.setting_file_loader_action import SettingFileLoaderAction

parser = argparse.ArgumentParser()
parser.add_argument(
    "--stage-settings",
    type=str,
    dest="settings",
    default=os.path.join(os.path.dirname(__file__), "data", "default.stage.json"),
    action=SettingFileLoaderAction,
    help="Stage setting description JSON or YAML file path or string object.",
)


@pytest.fixture
def default() -> dict:
    return {"all": {"tag": "<fluentd-tag>", "label": "<fluentd-label>"}}


def test_json_file(default):
    args = parser.parse_args(
        [
            "--stage-settings",
            os.path.join(os.path.dirname(__file__), "data", "default.json"),
        ]
    )
    assert args.settings == default


def test_yaml_file(default):
    args = parser.parse_args(
        [
            "--stage-settings",
            os.path.join(os.path.dirname(__file__), "data", "default.yaml"),
        ]
    )
    assert args.settings == default


def test_xml_error():
    with pytest.raises(ValueError):
        parser.parse_args(
            [
                "--stage-settings",
                os.path.join(os.path.dirname(__file__), "data", "default.xml"),
            ]
        )


def test_more_complex_json_file(default):
    args = parser.parse_args(
        [
            "--stage-settings",
            os.path.join(os.path.dirname(__file__), "data", "complex.json"),
        ]
    )
    assert args.settings == {
        "all": {"tag": "", "label": "", "drop": ["stage"]},
        "pytest_sessionstart": {
            "tag": "run",
            "label": "test",
            "replace": {"keys": {"sessionId": "id"}},
            "drop": ["status"],
            "add": {"root_id": "8dcf8f65-35a6-4b9e-af88-e3ec9743eab9"},
        },
        "pytest_sessionfinish": {
            "tag": "result",
            "label": "test",
            "replace": {"keys": {"sessionId": "id"}},
            "add": {
                "root_id": "8dcf8f65-35a6-4b9e-af88-e3ec9743eab9",
                "additional_information": {
                    "name": "super_complex",
                    "more": {"name": "more_data", "id": 1},
                },
            },
            "drop": ["status"],
        },
        "pytest_runtest_logstart": {
            "tag": "run",
            "label": "testcase",
            "replace": {"keys": {"sessionId": "root_id", "testId": "id"}},
            "drop": ["status"],
        },
        "pytest_runtest_logreport": {
            "tag": "result",
            "label": "testcase",
            "replace": {
                "keys": {"sessionId": "root_id", "testId": "id", "outcome": "result"}
            },
            "drop": ["status", "when", "markers"],
        },
        "logging": {
            "tag": "run",
            "label": "logging",
            "replace": {"keys": {"message": "msg", "sessionId": "id"}},
        },
    }
