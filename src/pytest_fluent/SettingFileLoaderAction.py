"""Package in order to train and test complex compression."""
import argparse
import json
from ruamel.yaml import YAML
import os

import jsonschema


class SettingFileLoaderAction(argparse.Action):
    """Custom action for loading JSON/YAML configuration."""

    def __call__(self, parser, args, values, option_string=None):
        """Implementing call."""
        parameter = values
        if parameter.endswith(".json"):
            pickle = json
        elif parameter.endswith(".yaml"):
            pickle = YAML()

            def loads(fp):
                return pickle.load(fp.read())

            pickle.__setattr__("loads", loads)
        else:
            raise ValueError("File type not supported.")
        if os.path.exists(parameter):
            with open(parameter) as fid:
                parameter = pickle.load(fid)
        else:
            parameter = pickle.loads(parameter)
        with open(
            os.path.join(os.path.dirname(__file__), "data", "schema.stage.json")
        ) as fid:
            schema = json.load(fid)
        jsonschema.validate(instance=parameter, schema=schema)
        setattr(args, self.dest, parameter)
