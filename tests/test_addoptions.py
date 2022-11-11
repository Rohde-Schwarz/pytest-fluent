import uuid

from fluent.sender import EventTime

from .mock_args_workaround import get_call_arg_args, get_call_arg_data


tag = "unittest"
label = "pytest"


def test_fluentd_logged_parameters(
    run_mocked_pytest, session_uuid, logging_content
):
    runpytest, sender = run_mocked_pytest
    result = runpytest(
        f"--session-uuid={session_uuid}",
        f"--fluentd-tag={tag}",
        f"--fluentd-label={label}",
        "--extend-logging",
    )
    fluent_sender = sender.return_value
    call_args = fluent_sender.emit_with_time.call_args_list
    result.assert_outcomes(passed=1)
    assert len(call_args) > 0
    for idx, call_arg in enumerate(call_args):
        args = get_call_arg_args(call_arg)
        if idx not in [2, 3]:
            assert args[0] == label
            assert isinstance(args[1], int)
        else:
            assert args[0] is None
            assert isinstance(args[1], EventTime)
        data = get_call_arg_data(call_arg)
        assert isinstance(data, dict)
        if idx in [0, 1]:
            assert data.get("status") == "start"
        if idx in [5, 6]:
            assert data.get("status") == "finish"
        assert data.get("sessionId") == str(session_uuid)
        if idx in [2, 3]:
            assert data.get("type") == "logging"
            assert "host" in data
            assert "where" in data
            assert "level" in data
            assert "stack_trace" in data
            assert data.get("message") == logging_content
        if idx in [0, 6]:
            assert data.get("stage") == "session"
        if idx in [1, 2, 3, 4, 5]:
            assert data.get("stage") == "testcase"
            assert "testId" in data
            try:
                uuid.UUID(data["testId"])
            except ValueError:
                assert False, "Not a UUID string"
