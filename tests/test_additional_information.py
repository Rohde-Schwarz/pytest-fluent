from pytest_fluent import (
    additional_session_information_callback,
    additional_test_information_callback,
)


@additional_session_information_callback
def session_info() -> dict:
    return {"type": "myCustomSession"}


@additional_test_information_callback
def test_info() -> dict:
    return {"type": "mySuperTestcase"}


def test_additional_information(run_mocked_pytest, session_uuid):
    runpytest, sender = run_mocked_pytest
    runpytest(f"--session-uuid={session_uuid}")
    fluent_sender = sender.return_value
    call_args = fluent_sender.emit_with_time.call_args_list
    for idx, call_arg in enumerate(call_args):
        data = call_arg.args[2]
        if idx == 0:
            assert data.get("type") == "myCustomSession"
        if idx == 1:
            assert data.get("type") == "mySuperTestcase"
