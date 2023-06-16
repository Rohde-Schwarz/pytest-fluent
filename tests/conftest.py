import uuid
from unittest.mock import MagicMock, patch

import pytest
from fluent import handler

import pytest_fluent.event

plugin_name = "pytest_fluent"
SESSION_UUID = uuid.uuid4()


def isinstance_patch(
    __obj: object,
    __class_or_tuple,
) -> bool:
    """Patch for isinstance."""
    if isinstance(__obj, MagicMock):
        return True
    return isinstance(__obj, __class_or_tuple)


@pytest.fixture(scope="session")
def logging_content():
    return "Logged from test_base"


@pytest.fixture(scope="session")
def session_uuid():
    return SESSION_UUID


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
def fluentd_sender(monkeypatch):
    """Get FluentSender mock."""
    with patch("pytest_fluent.event.FluentSender") as sender, patch.object(
        pytest_fluent.event, "isinstance", isinstance_patch
    ):
        monkeypatch.setattr(handler.sender, "FluentSender", sender)
        yield sender.return_value


@pytest.fixture()
def run_mocked_pytest(runpytest, fluentd_sender):
    """Create a temporary pytest environment with FluentSender mock."""

    return runpytest, fluentd_sender
