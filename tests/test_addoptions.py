import uuid

import pytest
from fluent.sender import EventTime

FLUENTD_TAG = "unittest"
FLUENTD_LABEL = "pytest"


def get_data_from_call_args(call_args, fields: list[str]) -> dict:
    return {field: call_args.args[2].get(field) for field in fields}


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
    message_0 = get_data_from_call_args(call_args[0], ["status", "stage"])
    assert message_0 == {"status": "start", "stage": "session"}

    # Message 1
    assert call_args[1].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[1].args[1], int)
    message_1 = get_data_from_call_args(call_args[1], ["status", "stage"])
    assert message_1 == {"status": "start", "stage": "testcase"}
    assert "testId" in call_args[1].args[2]
    try:
        uuid.UUID(call_args[1].args[2]["testId"])
    except ValueError as e:
        pytest.fail(f"{call_args[1].args[2]['testId']} is not a valid UUID: {e}")

    # Message 2
    assert call_args[2].args[0] is None
    assert isinstance(call_args[2].args[1], EventTime)
    message_2 = get_data_from_call_args(call_args[2], ["stage", "message"])
    assert message_2 == {"stage": "testcase", "message": logging_content}
    assert {"host", "where", "level", "stack_trace"}.issubset(
        call_args[2].args[2].keys()
    )

    # Message 3
    assert call_args[3].args[0] is None
    assert isinstance(call_args[3].args[1], EventTime)
    message_3 = get_data_from_call_args(call_args[2], ["type", "stage", "message"])
    assert message_3 == {
        "type": "logging",
        "stage": "testcase",
        "message": logging_content,
    }
    assert {"host", "where", "level", "stack_trace"}.issubset(
        call_args[2].args[2].keys()
    )

    # Message 4
    assert call_args[4].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[4].args[1], int)
    assert call_args[4].args[2].get("stage") == "testcase"

    # Message 5
    assert call_args[5].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[5].args[1], int)
    message_5 = get_data_from_call_args(call_args[5], ["status", "stage"])
    assert message_5 == {"status": "finish", "stage": "testcase"}

    # Message 6
    assert call_args[6].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[6].args[1], int)
    message_6 = get_data_from_call_args(call_args[6], ["status", "stage"])
    assert message_6 == {"status": "finish", "stage": "session"}
    assert call_args[6].args[2].get("duration") > 0


def test_fluentd_with_options_and_timestamp_enabled_shows_timestamp_field_in_output(
    runpytest, fluentd_sender, session_uuid
):
    result = runpytest(
        f"--session-uuid={session_uuid}",
        f"--fluentd-tag={FLUENTD_TAG}",
        f"--fluentd-label={FLUENTD_LABEL}",
        f"--fluentd-timestamp=@timestamp",
        "--extend-logging",
    )
    result.assert_outcomes(passed=1)
    call_args = fluentd_sender.emit_with_time.call_args_list
    assert len(call_args) == 7

    # TODO: figure out if this test is doing the right thing
    assert "@timestamp" in call_args[0].args[2]
    assert "@timestamp" in call_args[1].args[2]


def test_fluentd_with_timestamp_enabled_shows_timestamp_field_in_output(
    runpytest, fluentd_sender, session_uuid
):
    result = runpytest(
        f"--session-uuid={session_uuid}",
        f"--fluentd-timestamp=@timestamp",
    )
    result.assert_outcomes(passed=1)
    call_args = fluentd_sender.emit_with_time.call_args_list
    assert len(call_args) == 5

    # TODO: figure out if this test is doing the right thing
    assert "@timestamp" in call_args[0].args[2]
    assert "@timestamp" in call_args[1].args[2]
