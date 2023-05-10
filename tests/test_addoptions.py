import uuid

import pytest
from fluent.sender import EventTime

FLUENTD_TAG = "unittest"
FLUENTD_LABEL = "pytest"


def test_fluentd_logged_parameters(
    runpytest, fluentd_sender, session_uuid, logging_content
):
    result = runpytest(
        f"--session-uuid={session_uuid}",
        f"--fluentd-tag={FLUENTD_TAG}",
        f"--fluentd-label={FLUENTD_LABEL}",
        "--extend-logging",
    )
    call_args = fluentd_sender.emit_with_time.call_args_list
    result.assert_outcomes(passed=1)
    assert len(call_args) == 7

    # Message 0
    assert call_args[0].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[0].args[1], int)
    assert call_args[0].args[2].get("status") == "start"
    assert call_args[0].args[2].get("stage") == "session"

    # Message 1
    assert call_args[1].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[1].args[1], int)
    assert call_args[1].args[2].get("status") == "start"
    assert call_args[1].args[2].get("stage") == "testcase"
    assert "testId" in call_args[1].args[2]
    try:
        uuid.UUID(call_args[1].args[2]["testId"])
    except ValueError as e:
        pytest.fail(f"{call_args[1].args[2]['testId']} is not a valid UUID: {e}")

    # Message 2
    assert call_args[2].args[0] is None
    assert isinstance(call_args[2].args[1], EventTime)
    assert call_args[2].args[2].get("stage") == "testcase"
    assert call_args[2].args[2].get("message") == logging_content
    assert "host" in call_args[2].args[2]
    assert "where" in call_args[2].args[2]
    assert "level" in call_args[2].args[2]
    assert "stack_trace" in call_args[2].args[2]

    # Message 3
    assert call_args[3].args[0] is None
    assert isinstance(call_args[3].args[1], EventTime)
    assert call_args[3].args[2].get("type") == "logging"
    assert call_args[3].args[2].get("stage") == "testcase"
    assert call_args[3].args[2].get("message") == logging_content
    assert "host" in call_args[3].args[2]
    assert "where" in call_args[3].args[2]
    assert "level" in call_args[3].args[2]
    assert "stack_trace" in call_args[3].args[2]

    # Message 4
    assert call_args[4].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[4].args[1], int)
    assert call_args[4].args[2].get("stage") == "testcase"

    # Message 5
    assert call_args[5].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[5].args[1], int)
    assert call_args[5].args[2].get("stage") == "testcase"
    assert call_args[5].args[2].get("status") == "finish"

    # Message 6
    assert call_args[6].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[6].args[1], int)
    assert call_args[6].args[2].get("stage") == "session"
    assert call_args[6].args[2].get("status") == "finish"
    assert call_args[6].args[2].get("duration") > 0


def test_fluentd_with_timestamp_enabled_shows_timestamp_field_in_output(
    runpytest, fluentd_sender, session_uuid
):
    result = runpytest(
        f"--session-uuid={session_uuid}",
        f"--fluentd-tag={FLUENTD_TAG}",
        f"--fluentd-label={FLUENTD_LABEL}",
        f"--fluentd-timestamp='@timestamp'",
        "--extend-logging",
    )
    result.assert_outcomes(passed=1)
    call_args = fluentd_sender.emit_with_time.call_args_list
    assert len(call_args) == 7

    for data_fields in call_args:
        assert "timestamp" in data_fields.args[2]
