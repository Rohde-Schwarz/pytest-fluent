import argparse
import json
import os
from io import StringIO

import pytest
from pytest_fluent.setting_file_loader_action import SettingFileLoaderAction
from ruamel.yaml import YAML

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


@pytest.fixture(scope="session")
def complex() -> dict:
    with open(
        os.path.join(os.path.dirname(__file__), "data", "complex.json"),
        mode="r",
        encoding="utf-8",
    ) as fp:
        return json.load(fp)


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
    with pytest.raises(
        ValueError, match="Wrong input format or file type not supported."
    ):
        parser.parse_args(
            [
                "--stage-settings",
                os.path.join(os.path.dirname(__file__), "data", "default.xml"),
            ]
        )


def test_more_complex_json_file(complex):
    args = parser.parse_args(
        [
            "--stage-settings",
            os.path.join(os.path.dirname(__file__), "data", "complex.json"),
        ]
    )
    assert args.settings == complex


def test_more_complex_json_string(complex):
    args = parser.parse_args(
        [
            "--stage-settings",
            f"json;{json.dumps(complex, indent=0)}",
        ]
    )
    assert args.settings == complex


def test_more_complex_yaml_string(complex):
    yaml = YAML()
    io = StringIO()
    yaml.dump(complex, io)
    args = parser.parse_args(
        [
            "--stage-settings",
            f"yaml;{io.getvalue()}",
        ]
    )
    assert args.settings == complex


def test_wrong_input_format():
    with pytest.raises(
        ValueError, match="Wrong input format or file type not supported."
    ):
        parser.parse_args(
            [
                "--stage-settings",
                "abc-def",
            ]
        )
