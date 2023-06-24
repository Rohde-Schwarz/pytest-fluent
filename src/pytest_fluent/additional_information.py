"""Set additional information function handler."""
import inspect
import typing

INFORMATION_CALLBACKS: typing.Dict[str, typing.List[typing.Callable]] = {}
SESSION_STAGE = "pytest_sessionstart"
TEST_STAGE = "pytest_runtest_logstart"


def additional_information_callback(stage_name: str):
    """Set custom information callback for any stage.

    Args:
        stage_name (str): Linked stage name.
    """

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
    if stage in INFORMATION_CALLBACKS:
        INFORMATION_CALLBACKS[stage].append(function)
    else:
        INFORMATION_CALLBACKS[stage] = [function]


def get_additional_information_callback(
    stage: typing.Optional[str] = None,
) -> typing.Dict[str, typing.Any]:
    """Retrieve stage information from callable.

    Args:
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
    for function in functions:
        sub_info = function()
        if not isinstance(sub_info, dict):
            continue
        info.update(sub_info)
    return info
