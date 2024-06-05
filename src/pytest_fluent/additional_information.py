"""Set additional information function handler."""

import inspect
import typing

import pytest

INFORMATION_CALLBACKS: typing.Dict[str, typing.List[typing.Callable[..., dict]]] = {}
SESSION_STAGE = "pytest_sessionstart"
TEST_STAGE = "pytest_runtest_logstart"
SUPPORTED_STAGES = [
    "pytest_sessionstart",
    "pytest_sessionfinish",
    "pytest_runtest_logstart",
    "pytest_runtest_logreport",
    "pytest_runtest_logfinish",
]


def additional_information_callback(stage_name: str):
    """Set custom information callback for any stage.

    Args:
        stage_name (str): Linked stage name.
    """
    if stage_name not in SUPPORTED_STAGES:
        raise ValueError(f"Stage name {stage_name} not supported.")

    def wrapper(function: typing.Callable):
        set_additional_information_callback(stage_name, function)
        return function

    return wrapper


def additional_session_information_callback(function: typing.Callable):
    """Set callback for session information.

    Args:
        function (typing.Callable): Callable for test session information.
    """
    set_additional_information_callback(SESSION_STAGE, function)


def additional_test_information_callback(function: typing.Callable):
    """Set callback for test information.

    Args:
        function (typing.Callable): Callable for test session information.
    """
    set_additional_information_callback(TEST_STAGE, function)


def set_additional_information_callback(
    stage: str,
    function: typing.Callable,
) -> None:
    """Set callable for specific stage.

    Args:
        stage (str): Stage name.
        function (typing.Callable): Callback function.
    """
    check_allowed_input(function)
    if stage in INFORMATION_CALLBACKS:
        INFORMATION_CALLBACKS[stage].append(function)
    else:
        INFORMATION_CALLBACKS[stage] = [function]


def get_additional_information_callback(
    item: typing.Optional[pytest.Item] = None,
    stage: typing.Optional[str] = None,
) -> typing.Dict[str, typing.Any]:
    """Retrieve stage information from callable.

    Args:
        item (typing.Optional[pytest.Item], optional): Current testcase item.
        stage (typing.Optional[str], optional): Stage name. Defaults to None.

    Returns:
        typing.Dict[str, typing.Any]: Additional information dictionary.
    """
    # If stage name is not provided directly, get calling stage name via reflection
    if stage is None:
        stage = inspect.stack()[1][3]
    info: typing.Dict[str, typing.Any] = {}
    functions = INFORMATION_CALLBACKS.get(stage)
    if functions is None:
        return info
    for function in typing.cast(typing.List[typing.Callable[..., dict]], functions):
        annotations = function.__annotations__
        if "item" in annotations and annotations["item"] is pytest.Item:
            sub_info = function(item)
        else:
            sub_info = function()
        info.update(sub_info)
    return info


def check_type_with_optional(
    annotation: typing.Any, exptected_type: typing.Type
) -> bool:
    """Check if is type with optional.

    Args:
        annotation (typing.Any): Annotation to check
        exptected_type (typing.Type): Expected type

    Returns:
        bool: True if it is the expected type.
    """
    is_t = annotation is exptected_type
    is_opt_t = annotation is typing.Optional[exptected_type]
    return is_t or is_opt_t


def check_allowed_input(func: typing.Callable) -> None:
    """Check that the given function has a specific signature.

    Args:
        func (typing.Callable): The function to check.
    """
    if not callable(func):
        raise TypeError("Not a function")
    annotations = func.__annotations__
    args = set(annotations.keys())
    if "item" in args and not check_type_with_optional(
        annotations["item"], pytest.Item
    ):
        raise TypeError("Invalid function signature for 'item'")
    if not ("return" in args and annotations["return"] is dict):
        raise TypeError("Invalid function signature for return type. Expecting a dict.")
