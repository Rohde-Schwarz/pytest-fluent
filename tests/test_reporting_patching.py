import json

import pytest

from .conftest import SESSION_UUID


@pytest.mark.parametrize(
    "patch_file_content,expected_result,extend_logging",
    [
        (
            {"all": {"tag": "<fluentd-tag>", "label": "<fluentd-label>"}},
            [
                {
                    "status": "start",
                    "stage": "session",
                    "sessionId": str(SESSION_UUID),
                },
                {
                    "status": "start",
                    "stage": "testcase",
                    "sessionId": str(SESSION_UUID),
                    "name": "test_data_reporter_with_patched_values.py::test_base",
                },
                {
                    "type": "logging",
                    "where": "test_data_reporter_with_patched_values.test_base",
                    "level": "INFO",
                    "stack_trace": "None",
                    "message": "Test running",
                    "sessionId": str(SESSION_UUID),
                    "stage": "testcase",
                },
                {
                    "name": "test_data_reporter_with_patched_values.py::test_base",
                    "outcome": "passed",
                    "stage": "testcase",
                    "when": "call",
                    "sessionId": str(SESSION_UUID),
                },
                {
                    "status": "finish",
                    "stage": "testcase",
                    "sessionId": str(SESSION_UUID),
                    "name": "test_data_reporter_with_patched_values.py::test_base",
                },
                {
                    "status": "finish",
                    "stage": "session",
                    "sessionId": str(SESSION_UUID),
                },
            ],
            True,
        ),
        (
            {
                "all": {
                    "tag": "<fluentd-tag>",
                    "label": "<fluentd-label>",
                    "replace": {
                        "keys": {"status": "state", "sessionId": "id"},
                    },
                    "drop": ["stage", "state"],
                },
                "pytest_runtest_logreport": {
                    "replace": {
                        "values": {"passed": "pass", "failed": "fail"},
                    },
                    "add": {"stop_info": "Testcase finished"},
                    "drop": ["when"],
                },
            },
            [
                {
                    "id": str(SESSION_UUID),
                },
                {
                    "id": str(SESSION_UUID),
                    "name": "test_data_reporter_with_patched_values.py::test_base",
                },
                {
                    "type": "logging",
                    "where": "test_data_reporter_with_patched_values.test_base",
                    "level": "INFO",
                    "stack_trace": "None",
                    "message": "Test running",
                    "id": str(SESSION_UUID),
                },
                {
                    "name": "test_data_reporter_with_patched_values.py::test_base",
                    "outcome": "pass",
                    "id": str(SESSION_UUID),
                    "stop_info": "Testcase finished",
                },
                {
                    "id": str(SESSION_UUID),
                    "name": "test_data_reporter_with_patched_values.py::test_base",
                },
                {
                    "id": str(SESSION_UUID),
                },
            ],
            True,
        ),
        (
            {
                "all": {
                    "tag": "",
                    "label": "",
                    "replace": {
                        "keys": {"status": "state", "sessionId": "id"},
                    },
                },
                "pytest_runtest_logreport": {
                    "tag": "<fluentd-tag>",
                    "label": "<fluentd-label>",
                    "replace": {
                        "values": {"passed": "pass", "failed": "fail"},
                    },
                    "add": {"stop_info": "Testcase finished"},
                    "drop": ["when"],
                },
            },
            [
                {
                    "name": "test_data_reporter_with_patched_values.py::test_base",
                    "outcome": "pass",
                    "stage": "testcase",
                    "id": str(SESSION_UUID),
                    "stop_info": "Testcase finished",
                }
            ],
            False,
        ),
    ],
)
def test_data_reporter_with_patched_values(
    pytester,
    run_mocked_pytest,
    session_uuid,
    patch_file_content,
    expected_result,
    extend_logging,
):
    runpytest, fluent_sender = run_mocked_pytest
    pytester.makefile(".json", patch_file=json.dumps(patch_file_content))
    log_content = "Test running"
    args = [
        f"--session-uuid={session_uuid}",
        "--stage-settings=patch_file.json",
    ]
    if extend_logging:
        args.append("--extend-logging")

    result = runpytest(
        *args,
        pyfile=f"""
    import logging

    def test_base():
        logger = logging.getLogger()
        logger.info("{log_content}")
        assert True
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    call_args = [x[0][2] for x in call_args]
    result.assert_outcomes(passed=1)
    assert len(call_args) == len(expected_result)
    for report, expected in zip(call_args, expected_result):
        for key in expected.keys():
            assert key in report
            if key in ["duration", "testId", "host", "markers"]:
                continue
            assert report[key] == expected[key]
