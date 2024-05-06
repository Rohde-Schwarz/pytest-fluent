"""Load and schema check settings file."""

import argparse
import json
import os
import re
import typing

import jsonschema
from ruamel.yaml import YAML


class SettingFileLoaderAction(argparse.Action):
    """Custom action for loading JSON/YAML configuration."""

    def __call__(self, parser, args, values, option_string=None):
        """Implement call."""
        parameter = load_and_check_settings_file(values)
        setattr(args, self.dest, parameter)


def load_and_check_settings_file(file_name: str) -> typing.Dict[str, typing.Any]:
    """Load settings file and check content against schema.

    Args:
        file_name (str): Path to settings file.

    Raises:
        ValueError: File type not supported.

    Returns:
        typing.Dict[str, typing.Any]: User settings dictionary.
    """
    if file_name.endswith(".json"):
        pickle = json
    elif file_name.endswith(".yaml"):
        pickle = YAML()

        def loads(file_pointer):
            stream = StringIO(file_pointer)
            return pickle.load(stream)

        setattr(pickle, "loads", loads)
    else:
        raise ValueError("Wrong input format or file type not supported.")
    if os.path.exists(file_data):
        with open(file_data, encoding="utf-8") as fid:
            content = pickle.load(fid)
    else:
        content = pickle.loads(file_data)
    with open(
        os.path.join(os.path.dirname(__file__), "data", "schema.stage.json"),
        encoding="utf-8",
    ) as fid:
        schema = json.load(fid)
    jsonschema.validate(instance=content, schema=schema)
    return content
