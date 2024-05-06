import json
import sys

import jsonschema
import pytest

if sys.version_info[:2] > (3, 8):
    from importlib.resources import files
else:
    from importlib_resources import files


pytest_fluent_resources = files("pytest_fluent")
schema_file = pytest_fluent_resources / "data" / "schema.stage.json"
default_file = pytest_fluent_resources / "data" / "default.stage.json"


@pytest.fixture
def default() -> dict:
    with open(str(default_file), "r") as fp:
        default = json.load(fp)
    return default


@pytest.fixture
def schema() -> dict:
    with open(str(schema_file), "r") as fp:
        schema = json.load(fp)
    return schema


def test_default_compliance(default, schema):
    jsonschema.validate(default, schema)
    default["pytest_runtest_logstart"] = {"replace": {"status": "state"}}
    jsonschema.validate(default, schema)
    default["pytest_runtest_logstart"] = {"add": {"my_field": "${MY_FIELD}"}}
    jsonschema.validate(default, schema)
    default["pytest_runtest_logstart"] = {"tag": "<args.tag>", "label": "<args.label>"}
    jsonschema.validate(default, schema)


def test_default_compliance_fail(default, schema):
    default["any"] = {"tag": "x", "label": "y", "replace": {"where": "test"}}

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(default, schema)

    default["any"] = {"replace": {"where": "test"}}

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(default, schema)
