import typing
import uuid

import pytest
from fluent.sender import EventTime

FLUENTD_TAG = "unittest"
FLUENTD_LABEL = "pytest"


FAKE_TEST_UUID = "6d653fee-0c6a-4923-9216-dfc949bd05a0"


@pytest.fixture
def pyfile_testcase(logging_content):
    return f"""
import logging

def test_base():
    LOGGER = logging.getLogger()
    LOGGER.info('{logging_content}')
    LOGGER.warning('{logging_content}')
    assert True
"""


def get_data_from_call_args(call_args, fields: typing.List[str]) -> typing.Dict:
    return {field: call_args.args[2].get(field) for field in fields}


def test_fluentd_logged_parameters(
    monkeypatch, run_mocked_pytest, session_uuid, logging_content, pyfile_testcase
):
    runpytest, fluent_sender = run_mocked_pytest
    monkeypatch.setattr(uuid, "uuid4", lambda: uuid.UUID(FAKE_TEST_UUID))
    result = runpytest(
        f"--session-uuid={session_uuid}",
        f"--fluentd-tag={FLUENTD_TAG}",
        f"--fluentd-label={FLUENTD_LABEL}",
        "--extend-logging",
        pyfile=pyfile_testcase,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    result.assert_outcomes(passed=1)
    assert len(call_args) == 7

    # Message 0
    assert call_args[0].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[0].args[1], int)
    message_0 = get_data_from_call_args(call_args[0], ["status", "stage", "sessionId"])
    assert message_0 == {
        "status": "start",
        "stage": "session",
        "sessionId": f"{session_uuid}",
    }

    # Message 1
    assert call_args[1].args[0] == FLUENTD_LABEL
    assert isinstance(call_args[1].args[1], int)
    message_1 = get_data_from_call_args(call_args[1], ["status", "stage", "testId"])
    assert message_1 == {
        "status": "start",
        "stage": "testcase",
        "testId": FAKE_TEST_UUID,
    }

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


def is_pytest_message(args):
    return args[0] is not None and args[0] == "pytest"


def test_fluentd_with_options_and_timestamp_enabled_shows_timestamp_field_in_output(
    run_mocked_pytest, fluentd_sender, session_uuid, pyfile_testcase
):
    runpytest, fluentd_sender = run_mocked_pytest
    result = runpytest(
        f"--session-uuid={session_uuid}",
        f"--fluentd-tag={FLUENTD_TAG}",
        f"--fluentd-label={FLUENTD_LABEL}",
        "--fluentd-timestamp=@timestamp",
        "--extend-logging",
        pyfile=pyfile_testcase,
    )
    result.assert_outcomes(passed=1)
    call_args = fluentd_sender.emit_with_time.call_args_list
    assert len(call_args) == 7

    for call_arg in filter(is_pytest_message, call_args):
        assert "@timestamp" in call_arg.args[2]


def test_fluentd_with_timestamp_enabled_shows_timestamp_field_in_output(
    run_mocked_pytest, session_uuid, pyfile_testcase
):
    runpytest, fluentd_sender = run_mocked_pytest
    result = runpytest(
        f"--session-uuid={session_uuid}",
        "--fluentd-timestamp=@timestamp",
        pyfile=pyfile_testcase,
    )
    result.assert_outcomes(passed=1)
    call_args = fluentd_sender.emit_with_time.call_args_list
    assert len(call_args) == 5

    for call_arg in filter(is_pytest_message, call_args):
        assert "@timestamp" in call_arg.args[2]
