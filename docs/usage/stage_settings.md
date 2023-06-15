### Custom stage settings

Sometimes, the default settings are not enough in order to forward the test information as needed. Thus, you can set custom stage settings
in order to fit your needs.

You can set specific values for `all` stages or specific values for any used stage. In order to do so, call your test run with the `--stage-settings=YourFileName.json` parameter. The following example stage settings JSON file content

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

will result in the following output

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
    "host": "MU763729",
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

for this test case

```python
import logging

def test_base():
    logger = logging.getLogger()
    logger.info("Test running")
    assert True
```
