from pytest_fluent import (
    additional_information_callback,
    additional_session_information_callback,
    additional_test_information_callback,
)


def test_additional_information_convenience_wrapper(run_mocked_pytest, session_uuid):
    @additional_session_information_callback
    def session_info() -> dict:
        return {"type": "myCustomSession"}

    @additional_test_information_callback
    def test_info() -> dict:
        return {"type": "mySuperTestcase"}

    runpytest, fluent_sender = run_mocked_pytest
    runpytest(f"--session-uuid={session_uuid}")
    call_args = fluent_sender.emit_with_time.call_args_list
    for idx, call_arg in enumerate(call_args):
        data = call_arg.args[2]
        if idx == 0:
            assert data.get("type") == "myCustomSession"
        if idx == 1:
            assert data.get("type") == "mySuperTestcase"


def test_addtional_information_callbacks(run_mocked_pytest, session_uuid):
    @additional_information_callback("pytest_sessionstart")
    def session_info() -> dict:
        return {"type": "myCustomSession"}

    @additional_information_callback("pytest_runtest_logstart")
    def test_info() -> dict:
        return {"type": "mySuperTestcase"}

    runpytest, fluent_sender = run_mocked_pytest
    runpytest(f"--session-uuid={session_uuid}")
    call_args = fluent_sender.emit_with_time.call_args_list
    for idx, call_arg in enumerate(call_args):
        data = call_arg.args[2]
        if idx == 0:
            assert data.get("type") == "myCustomSession"
        if idx == 1:
            assert data.get("type") == "mySuperTestcase"


def test_multiple_addtional_information_callbacks_per_stage(
    run_mocked_pytest, session_uuid
):
    @additional_information_callback("pytest_sessionstart")
    def session_info() -> dict:
        return {"type": "myCustomSession"}

    @additional_information_callback("pytest_sessionstart")
    def test_info() -> dict:
        return {"super_type": "mySuperTestcase"}

    runpytest, fluent_sender = run_mocked_pytest
    runpytest(f"--session-uuid={session_uuid}")
    call_args = fluent_sender.emit_with_time.call_args_list
    for idx, call_arg in enumerate(call_args):
        data = call_arg.args[2]
        if idx == 0:
            assert data.get("type") == "myCustomSession"
            assert data.get("super_type") == "mySuperTestcase"
