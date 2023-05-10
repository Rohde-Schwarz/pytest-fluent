import uuid
from unittest.mock import patch

import pytest

plugin_name = "pytest_fluent"


@pytest.fixture(scope="session")
def logging_content():
    return "Logged from test_base"


@pytest.fixture(scope="session")
def session_uuid():
    return uuid.uuid4()


@pytest.fixture()
def runpytest(pytester: pytest.Pytester, logging_content):
    """create a temporary pytest environment with dummy test case."""

    def runpytest(*args, **kwargs):
        if "pyfile" in kwargs:
            pytester.makepyfile(kwargs.pop("pyfile"))
        else:
            pytester.makepyfile(
                f"""
    from logging import getLogger
    LOGGER = getLogger('fluent')

    def test_base():
        LOGGER.info('{logging_content}')
        assert True
    """
            )

        if "plugins" in kwargs:
            if not isinstance(kwargs["plugins"], list) and isinstance(
                kwargs["plugins"], str
            ):
                kwargs["plugins"] = [kwargs["plugins"]]
            if plugin_name not in kwargs["plugins"]:
                kwargs["plugins"].append(plugin_name)
            else:
                kwargs["plugins"] = [plugin_name]
        else:
            kwargs["plugins"] = [plugin_name]

        return pytester.runpytest(*args, **kwargs)

    return runpytest


@pytest.fixture()
def run_mocked_pytest(runpytest):
    """create a temporary pytest environment with FluentSender mock."""

    with patch("fluent.sender.FluentSender") as sender:
        yield runpytest, sender


@pytest.fixture()
def fluentd_sender():
    with patch("fluent.sender.FluentSender") as sender:
        yield sender.return_value
