# pytest-fluent

A Python package in order to extend pytest by fluentd logging

## Description

Pytest is one of the most powerful testing suites with a lot of functionality and many plugins. Fluentd is a well-established log collector which is used in many modern web architectures. So, why not putting both worlds together in order to gain real-time log access to your distributed test runs.

pytest-fluent enables you to forward your test data immediately to your prefered log-sink from any node spread around your infrastructure. The streamed data are available for each pytest stage and formatted in JSON.

Each pytest session gets an unique identifier (UID) assigned as well as each executed test case. With these UIDs, you can filter easily for sessions and testcase data entries, for instance in your favorite database.

## Installation

The package is available at pypi.rsint.net and can be installed by typing

```shell
pip install pytest-fluent
```

## Usage

pytest-fluent-logging forwards meta data from pytest to Fluentd for further processing. The meta data are 
* unique session ID
* unique test ID
* status of the session respectively test case
* test case name
* test results
* `record_property` entries
* custom testcase information
* custom session information
  
Furthermore, the Python logging instance can be extended in order to forward test case runtime logging.

```python
from logging import getLogger

def test_my_runtime_log():
    value = 1
    getLogger().info(f"Setting value to {value}")
    assert value == 1
```

or 

```python
from logging import getLogger

def test_my_runtime_log():
    value = 1
    getLogger('fluent').info(f"Setting value to {value}")
    assert value == 1
```

### Fixtures

In order to create your own logger, request the following fixture

```python
def test_my_runtime_log(get_logger):
    logger = get_logger('my.Logger')
    value = 1
    logger.info(f"Setting value to {value}")
    assert value == 1
```

If you want to get the current UIDs, use the following fixtures

```python
def test_unique_identifier(session_uid, test_uid):
    logger = get_logger('fluent')
    logger.info(f"Session ID: {session_uid}")
    logger.info(f"Test ID: {test_uid}")
    value = 1
    assert value == 1
```

### Callbacks

If you want to add custom data to the datasets of the `pytest_sessionstart` and `pytest_runtest_logstart` stages, decorate your callback functions with the following decorators.

```python
from pytest_fluent import (
    additional_session_information_callback,
    additional_test_information_callback
)

@additional_session_information_callback
def provide_more_session_information() -> dict:
    return {
        "more": "session information"
    }

@additional_test_information_callback
def provide_more_test_information() -> dict:
    return {
        "more": "test information"
    }
```

### pytest CLI extensions

The pytest CLI can be called with the following arguments in order to configure fluent-logging.

| argument         | description                                                                       | default  |
| ---------------- | --------------------------------------------------------------------------------- | -------- |
| --session-uuid   | Use a custom externally created UUID, e.g. link a CI job with the pytest session. |          |
| --fluentd-host   | Fluentd host address. If not provided, a local Fluentd instance will be called.   |          |
| --fluentd-port   | Fluent host port                                                                  | 24224    |
| --fluentd-tag    | Set a custom Fluentd tag                                                          | 'test'   |
| --fluentd-label  | Set a custom Fluentd label                                                        | 'pytest' |
| --extend-logging | Extend the Python logging with a Fluent handler                                   | False    |

### What data are sent?

pytest-fluent sends any information, e.g. stage information or logging from a test case, as a single chunk. For instance, the data collection from `test_addoptions.py` test looks as following

```json
[
    {
        "status": "start",
        "stage": "session",
        "sessionId": "d8f01de3-8416-4801-9406-0ea3d5cfe3c0"
    },
    {
        "status": "start",
        "stage": "testcase",
        "sessionId": "d8f01de3-8416-4801-9406-0ea3d5cfe3c0",
        "testId": "6b444275-4450-4eff-b5d9-8355f0f99ab0",
        "name": "test_fluentd_logged_parameters.py::test_base"
    },
    {
        "type": "logging",
        "host": "myComputer",
        "where": "test_fluentd_logged_parameters.test_base",
        "level": "INFO",
        "stack_trace": "None",
        "message": "Logged from test_base",
        "sessionId": "d8f01de3-8416-4801-9406-0ea3d5cfe3c0",
        "testId": "6b444275-4450-4eff-b5d9-8355f0f99ab0",
        "stage": "testcase"
    },
    {
        "type": "logging",
        "host": "myComputer",
        "where": "test_fluentd_logged_parameters.test_base",
        "level": "INFO",
        "stack_trace": "None",
        "message": "Logged from test_base",
        "sessionId": "d8f01de3-8416-4801-9406-0ea3d5cfe3c0",
        "testId": "6b444275-4450-4eff-b5d9-8355f0f99ab0",
        "stage": "testcase"
    },
    {
        "name": "test_fluentd_logged_parameters.py::test_base",
        "outcome": "passed",
        "duration": 0.0013457999999999526,
        "markers": {
            "test_base": 1,
            "test_fluentd_logged_parameters.py": 1,
            "test_fluentd_logged_parameters0": 1
        },
        "stage": "testcase",
        "when": "call",
        "sessionId": "d8f01de3-8416-4801-9406-0ea3d5cfe3c0",
        "testId": "6b444275-4450-4eff-b5d9-8355f0f99ab0"
    },
    {
        "status": "finish",
        "stage": "testcase",
        "sessionId": "d8f01de3-8416-4801-9406-0ea3d5cfe3c0",
        "testId": "6b444275-4450-4eff-b5d9-8355f0f99ab0",
        "name": "test_fluentd_logged_parameters.py::test_base"
    },
    {
        "status": "finish",
        "stage": "session",
        "sessionId": "d8f01de3-8416-4801-9406-0ea3d5cfe3c0"
    }
]
```

whereat each object in the array is sent independently via Fluentd.


## Changelog

The changelog.

## Contributing

We welcome any contributions, enhancements, and bug-fixes. Open an [issue](https://github.com/Rohde-Schwarz/pytest-fluent/issues) on [Github](https://github.com) and [submit a pull request](https://github.com/Rohde-Schwarz/pytest-fluent/pulls).

