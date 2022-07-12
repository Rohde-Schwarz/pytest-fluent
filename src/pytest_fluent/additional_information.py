import typing

session_information_callback: typing.Optional[typing.Callable] = None
test_information_callback: typing.Optional[typing.Callable] = None


def additional_session_information_callback(fn):
    global session_information_callback
    session_information_callback = fn


def additional_test_information_callback(fn):
    global test_information_callback
    test_information_callback = fn


def get_additional_session_information() -> dict:
    return get_additional_information(session_information_callback)


def get_additional_test_information() -> dict:
    return get_additional_information(test_information_callback)


def get_additional_information(fn: typing.Optional[typing.Callable]) -> dict:
    if fn is None:
        return {}
    info = fn()
    if not isinstance(info, dict):
        return {}
    return info
