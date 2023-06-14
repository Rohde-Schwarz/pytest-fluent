"""Load and schema check settings file."""
import argparse
import json
import os

import jsonschema
from ruamel.yaml import YAML


class SettingFileLoaderAction(argparse.Action):
    """Custom action for loading JSON/YAML configuration."""

    def __call__(self, parser, args, values, option_string=None):
        """Implementing call."""
        parameter = load_and_check_settings_file(values)
        setattr(args, self.dest, parameter)


def load_and_check_settings_file(file_name: str):
    """Load settings file and check content against schema.

    Args:
        file_name (str): Path to settings file.

    Raises:
        ValueError: File type not supported.

    Returns:
        _type_: User settings dictionary.
    """
    if file_name.endswith(".json"):
        pickle = json
    elif file_name.endswith(".yaml"):
        pickle = YAML()

        def loads(file_pointer):
            return pickle.load(file_pointer.read())

        setattr(pickle, "loads", loads)
    else:
        raise ValueError("File type not supported.")
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as fid:
            content = pickle.load(fid)
    else:
        content = pickle.loads(file_name)
    with open(
        os.path.join(os.path.dirname(__file__), "data", "schema.stage.json"),
        encoding="utf-8",
    ) as fid:
        schema = json.load(fid)
    jsonschema.validate(instance=content, schema=schema)
    return content
