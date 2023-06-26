### Custom stage settings

Sometimes, the default settings are not enough in order to forward the test information as needed. Therefore, you can set custom stage settings
in order to fit your needs.

You can set specific values for `all` stages or specific values for any used stage. In order to do so, call your test run with the `--stage-settings=YourFileName.json` parameter. The following example stage settings JSON file content:

```json
{
    "all": {
        "tag": "run",
        "label": "pytest",
        "replace": {"keys": {"status": "state", "sessionId": "id"}},
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
        "replace": {
            "values": {"passed": "pass", "failed": "fail"},
        },
        "add": {"stop_info": "Testcase finished"},
    },
    "logging": {
        "replace": {"keys": {"message": "msg", "sessionId": "id"}},
    },
}
```

will result in the following output:

```json
[
  {
    "stage": "session",
    "tag": "test",
    "label": "pytest",
    "state": "start",
    "id": "3d82b514-60e2-4580-96ab-3daf5a5446c8"
  },
  {
    "stage": "testcase",
    "testId": "6b5092ad-c905-4879-a70c-cb5b2a7df90d",
    "name": "test_data_reporter_with_patched_values.py::test_base",
    "tag": "test",
    "label": "pytest",
    "state": "start",
    "id": "3d82b514-60e2-4580-96ab-3daf5a5446c8"
  },
  {
    "type": "logging",
    "host": "hostname",
    "where": "test_data_reporter_with_patched_values.test_base",
    "level": "INFO",
    "stack_trace": "None",
    "message": "Test running",
    "testId": "6b5092ad-c905-4879-a70c-cb5b2a7df90d",
    "stage": "testcase",
    "id": "3d82b514-60e2-4580-96ab-3daf5a5446c8"
  },
  {
    "name": "test_data_reporter_with_patched_values.py::test_base",
    "outcome": "pass",
    "duration": 0.0034263000000001043,
    "markers": {
      "test_base": 1,
      "test_data_reporter_with_patched_values.py": 1,
      "test_data_reporter_with_patched_values0": 1
    },
    "stage": "testcase",
    "when": "call",
    "testId": "6b5092ad-c905-4879-a70c-cb5b2a7df90d",
    "tag": "test",
    "label": "pytest",
    "id": "3d82b514-60e2-4580-96ab-3daf5a5446c8",
    "stop_info": "Testcase finished"
  },
  {
    "stage": "testcase",
    "testId": "6b5092ad-c905-4879-a70c-cb5b2a7df90d",
    "name": "test_data_reporter_with_patched_values.py::test_base",
    "tag": "test",
    "label": "pytest",
    "state": "finish",
    "id": "3d82b514-60e2-4580-96ab-3daf5a5446c8"
  },
  {
    "duration": 1.3674933910369873,
    "stage": "session",
    "tag": "test",
    "label": "pytest",
    "state": "finish",
    "id": "3d82b514-60e2-4580-96ab-3daf5a5446c8"
  }
]
```

for this test case:

```python
import logging

def test_base():
    logger = logging.getLogger()
    logger.info("Test running")
    assert True
```

#### Stage setting file

Custom settings for each supported stage can be easily setup. You have to create a file with
a `.json` or `.yaml` extension and call pytest with this additional parameter `--stage-settings`.

The file will be validated against a schema of supported values and in case of an error, a `jsonschema.ValidationError`
will be thrown.

#### Stage settings

##### Number of supported stage

The following stages can be modified.

* `pytest_sessionstart`
* `pytest_runtest_logstart`
* `pytest_runtest_logreport`
* `pytest_runtest_logfinish`
* `pytest_sessionfinish`
* `logging`

These values are the keys for the dictionary object. Additionally, you can set also
a `all` key for convenience reasons to patch all keys at once.

#### Patch events

Probably, your stage setting would look like

```json
{
    "pytest_sessionstart": {
        "tag": "run",
        "label": "pytest",
        "replace": {
            "keys": {
                "status": "state",
                "sessionId": "id"
            },
            "values": {
                "passed": "pass"
            }
        },
        "add": {
          "start_info": "Pytest started"
        },
    }
}
```

The following values are supported:

| Key name  | action                                                                                 | type             |
| --------- | -------------------------------------------------------------------------------------- | ---------------- |
| `tag`     | Set a specifc Fluent tag for this stage                                                | `str`            |
| `label`   | Set a specifc Fluent label for this stage                                              | `str`            |
| `replace` | Replace key values from a dictionary and also replace some preset pytest result values | `Dict[str, str]` |
| `add`     | Add new values to the result dictionary                                                | `Dict[str, str]` |
| `drop`    | Drop specific values from the result dictionary                                        | `List[str]`      |

##### Suppressing stage forwarding

If you want that forwarding of a specific stage is suppressed, just set an empty string as `tag`.

For instance if you want just a single stage being forwarded, see the following example

```json
{
    "all": {
        "tag": ""
    },
    "pytest_runtest_logreport": {
        "tag": "run",
        "label": "pytest"
    }
}
```

##### Replace dictionary

The `replace` patching action has two keys `keys` and `values` in order to replace either a key value or a result value.
See the following default values in order to get an idea about the content.

At the moment, the following values can be changed

* `passed`
* `failed`
* `skipped`
* `error`
* `start`
* `finish`
* `session`
* `testcase`

##### Use values from ARGV and ENV

If you want to use data provided by the command line arguments or directly from environment variables,
use the following syntax for value strings.

| Type | Syntax                         |
| ---- | ------------------------------ |
| ARGV | `"<fluentd-tag>"`              |
| ENV  | `"${USE_ENV}"` or `"$USE_ENV"` |

Here is a simple example using both variants

```json
{
    "pytest_sessionstart": {
        "tag": "run",
        "label": "pytest",
        "replace": {
            "keys": {
                "tag": "<fluentd-tag>",
                "sessionId": "${ID}"
            },
            "values": {
                "passed": "$OUTCOME_PASSED"
            }
        }
    }
}
```

The data will be mapped after starting the pytest session.

#### Default values

| stage                      | value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pytest_sessionstart`      | <pre lang="json">{<br>    "status": "start",<br>    "stage": "session",<br>    "sessionId": "8d0d165d-5581-478c-ba0f-f7ec7d5bcbcf",<br>    "tag": "test",<br>    "label": "pytest"<br>}</pre>                                                                                                                                                                                                                                                                                                                                                                           |
| `pytest_runtest_logstart`  | <pre lang="json">{<br>    "status": "start",<br>    "stage": "testcase",<br>    "sessionId": "8d0d165d-5581-478c-ba0f-f7ec7d5bcbcf",<br>    "testId": "9f0363fa-ef99-49c7-8a2d-6261e90acb00",<br>    "name": "test_data_reporter_with_patched_values.py::test_base",<br>    "tag": "test",<br>    "label": "pytest"<br>}</pre>                                                                                                                                                                                                                                          |
| `pytest_runtest_logreport` | <pre lang="json">{<br>    "name": "test_data_reporter_with_patched_values.py::test_base",<br>    "outcome": "passed",<br>    "duration": 0.0035069000000005346,<br>    "markers": {<br>      "test_base": 1,<br>      "test_data_reporter_with_patched_values.py": 1,<br>      "test_data_reporter_with_patched_values0": 1<br>    },<br>    "stage": "testcase",<br>    "when": "call",<br>    "sessionId": "8d0d165d-5581-478c-ba0f-f7ec7d5bcbcf",<br>    "testId": "9f0363fa-ef99-49c7-8a2d-6261e90acb00",<br>    "tag": "test",<br>    "label": "pytest"<br>}</pre> |
| `pytest_runtest_logfinish` | <pre lang="json">{<br>    "status": "finish",<br>    "stage": "testcase",<br>    "sessionId": "8d0d165d-5581-478c-ba0f-f7ec7d5bcbcf",<br>    "testId": "9f0363fa-ef99-49c7-8a2d-6261e90acb00",<br>    "name": "test_data_reporter_with_patched_values.py::test_base",<br>    "tag": "test",<br>    "label": "pytest"<br>}</pre>                                                                                                                                                                                                                                         |
| `pytest_sessionfinish`     | <pre lang="json">{<br>    "status": "finish",<br>    "duration": 1.5651893615722656,<br>    "stage": "session",<br>    "sessionId": "8d0d165d-5581-478c-ba0f-f7ec7d5bcbcf",<br>    "tag": "test",<br>    "label": "pytest"<br>}</pre>                                                                                                                                                                                                                                                                                                                                   |
| `logging`                  | <pre lang="json">{<br>    "type": "logging",<br>    "host": "hostname",<br>    "where": "test_data_reporter_with_patched_values.test_base",<br>    "level": "INFO",<br>    "stack_trace": "None",<br>    "message": "Test running",<br>    "sessionId": "8d0d165d-5581-478c-ba0f-f7ec7d5bcbcf",<br>    "testId": "9f0363fa-ef99-49c7-8a2d-6261e90acb00",<br>    "stage": "testcase"<br>}</pre>                                                                                                                                                                          |
