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
    return {"all": {"tag": "<args.tag>", "label": "<args.label>"}}


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
