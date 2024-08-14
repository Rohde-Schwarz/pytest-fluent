import typing
from unittest.mock import patch

import pytest
import pytest_fluent.additional_information
from pytest_fluent import (
    additional_information_callback,
    additional_session_information_callback,
    additional_test_information_callback,
)
from pytest_fluent.additional_information import check_allowed_input


def test_allowed_input():
    def add_1() -> dict:
        return {}

    def add_2(item: pytest.Item) -> dict:
        return {}

    def add_2_opt(item: typing.Optional[pytest.Item] = None) -> dict:
        return {}

    def add_3(item: int) -> dict:
        return {}

    def add_4() -> int:
        return 1

    check_allowed_input(add_1)
    check_allowed_input(add_2)
    check_allowed_input(add_2_opt)

    with pytest.raises(TypeError, match="Invalid function signature for 'item'"):
        check_allowed_input(add_3)

    with pytest.raises(
        TypeError, match="Invalid function signature for return type. Expecting a dict."
    ):
        check_allowed_input(add_4)

    with pytest.raises(TypeError, match="Not a function"):
        check_allowed_input(1)  # type: ignore


@patch.object(pytest_fluent.additional_information, "INFORMATION_CALLBACKS", new={})
def test_additional_information_not_supported(
    run_mocked_pytest, session_uuid, logging_content
):
    with pytest.raises(ValueError):

        @additional_information_callback("test")
        def test_info() -> dict:
            return {"type": "myCustomSession"}


@patch.object(pytest_fluent.additional_information, "INFORMATION_CALLBACKS", new={})
def test_additional_information_convenience_wrapper(
    run_mocked_pytest, session_uuid, logging_content
):
    @additional_session_information_callback
    def session_info() -> dict:
        return {"type": "myCustomSession"}

    @additional_test_information_callback
    def test_info() -> dict:
        return {"type": "mySuperTestcase"}

    @additional_test_information_callback
    def test_info_more(item: pytest.Item) -> dict:
        if not isinstance(item, pytest.Item):
            return {}
        marker = [mark for mark in item.own_markers if mark.name == "testcase_id"]
        testcase_id = None
        if len(marker) > 0:
            mark = marker[0]
            if "id" in mark.kwargs:
                testcase_id = mark.kwargs["id"]
            elif len(mark.args) > 0:
                testcase_id = mark.args[0]

        return {"testcase": {"name": item.nodeid, "id": testcase_id}}

    runpytest, fluent_sender = run_mocked_pytest
    runpytest(
        f"--session-uuid={session_uuid}",
        pyfile=f"""
    from logging import getLogger
    import pytest
    LOGGER = getLogger('fluent')

    @pytest.mark.testcase_id(id="1a2b06a4-d902-4d63-9ae1-c16a63e7a9b8")
    def test_base():
        LOGGER.info('{logging_content}')
        assert True
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    for idx, call_arg in enumerate(call_args):
        data = call_arg.args[2]
        if idx == 0:
            assert data.get("type") == "myCustomSession"
        if idx == 1:
            assert data.get("type") == "mySuperTestcase"
            assert data.get("testcase") == {
                "name": "test_additional_information_convenience_wrapper.py::test_base",
                "id": "1a2b06a4-d902-4d63-9ae1-c16a63e7a9b8",
            }


@patch.object(pytest_fluent.additional_information, "INFORMATION_CALLBACKS", new={})
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


@patch.object(pytest_fluent.additional_information, "INFORMATION_CALLBACKS", new={})
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
