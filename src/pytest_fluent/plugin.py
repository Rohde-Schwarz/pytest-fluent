"""pytest-fluent-logging plugin definition."""
import logging
import typing
import uuid
from io import BytesIO

import msgpack
import pytest
from fluent import event, sender
from fluent.handler import FluentHandler, FluentRecordFormatter

from .additional_information import (
    get_additional_session_information,
    get_additional_test_information,
)
from .test_report import LogReport

#####################################################
# Plugin runtime
#####################################################


class FluentLoggerRuntime(object):
    def __init__(self, config):
        self._session_uuid = None
        self._test_uuid = None
        self.config = config
        self._set_session_uid(self.config.getoption("--session-uuid"))
        self._host = config.getoption("--fluentd-host")
        self._port = config.getoption("--fluentd-port")
        self._tag = config.getoption("--fluentd-tag")
        self._label = config.getoption("--fluentd-label")
        self._extend_logging = config.getoption("--extend-logging")
        self._log_reporter = LogReport(self.config)
        self._setup_fluent_sender()
        self._patch_logging()

    def _setup_fluent_sender(self):
        if self._host is None:
            sender.setup(self._tag, buffer_overflow_handler=overflow_handler)
        else:
            sender.setup(
                self._tag,
                host=self._host,
                port=self._port,
                buffer_overflow_handler=overflow_handler,
            )

    def _patch_logging(self):
        if self._extend_logging:
            extend_loggers(self._host, self._port, self._tag)

    def _set_session_uid(
        self, id: typing.Optional[typing.Union[str, uuid.UUID]] = None
    ) -> None:
        """Set or create a session ID."""
        if id is None:
            self._session_uuid = create_unique_identifier()
        elif isinstance(id, str):
            self._session_uuid = uuid.UUID(id)
        elif isinstance(id, uuid.UUID):
            self._session_uuid = id
        else:
            raise ValueError("Unique identifier is not in a valid format.")

    @property
    def session_uid(
        self,
    ) -> str:
        """Get current session ID."""
        return str(self._session_uuid)

    def _create_test_unique_identifier(self) -> None:
        """Create a new test ID."""
        self._test_uuid = create_unique_identifier()

    @property
    def test_uid(self) -> str:
        """Get current test ID."""
        return str(self._test_uuid)

    def pytest_sessionstart(self):
        """Custom hook for session start."""
        set_stage("session")
        if not self.config.getoption("collectonly"):
            data = {
                "status": "start",
                "stage": "session",
                "sessionId": self.session_uid,
            }
            data.update(get_additional_session_information())
            event.Event(self._label, data)

    def pytest_runtest_logstart(
        self, nodeid: str, location: typing.Tuple[int, str]
    ):
        """Custom hook for test start."""
        set_stage("testcase")
        if not self.config.getoption("collectonly"):
            self._create_test_unique_identifier()
            data = {
                "status": "start",
                "stage": "testcase",
                "sessionId": self.session_uid,
                "testId": self.test_uid,
                "name": nodeid,
            }
            data.update(get_additional_test_information())
            event.Event(self._label, data)

    def pytest_runtest_setup(self, item: pytest.Item):
        """Custom hook for test setup."""
        set_stage("testcase")
        if not self.config.getoption("collectonly"):
            pass

    def pytest_runtest_call(self, item: pytest.Item):
        """Custom hook for test call."""
        set_stage("testcase")
        if not self.config.getoption("collectonly"):
            pass

    def pytest_runtest_logreport(self, report: pytest.TestReport):
        """Custom hook for logging results."""
        set_stage("testcase")
        if not self.config.getoption("collectonly"):
            result_data = self._log_reporter(report)
            if not result_data:
                return
            result_data.update(
                {
                    "stage": "testcase",
                    "when": report.when,
                    "sessionId": self.session_uid,
                    "testId": self.test_uid,
                }
            )
            event.Event(self._label, result_data)

    def pytest_runtest_logfinish(
        self,
        nodeid: str,
        location: typing.Tuple[str, typing.Optional[int], str],
    ):
        """Custom hook for test end."""
        set_stage("testcase")
        if not self.config.getoption("collectonly"):
            event.Event(
                self._label,
                {
                    "status": "finish",
                    "stage": "testcase",
                    "sessionId": self.session_uid,
                    "testId": self.test_uid,
                    "name": nodeid,
                },
            )

    def pytest_sessionfinish(
        self,
        session: pytest.Session,
        exitstatus: typing.Union[int, pytest.ExitCode],
    ):
        """Custom hook for session end."""
        set_stage("session")
        if not self.config.getoption("collectonly"):
            event.Event(
                self._label,
                {
                    "status": "finish",
                    "stage": "session",
                    "sessionId": self.session_uid,
                },
            )


stage: str = "session"
fluent_runtime: typing.Optional[FluentLoggerRuntime] = None

#####################################################
# Setup
#####################################################


def pytest_addoption(parser):
    """Extend pytest addoption."""
    group = parser.getgroup("fluent-logging")
    group.addoption(
        "--session-uuid",
        default=None,
        help="Provide a unique session identifier for logging.",
    )
    group.addoption(
        "--fluentd-host",
        default=None,
        help="Fluentd remote host. Defaults to a local Fluentd session",
    )
    group.addoption(
        "--fluentd-port",
        default=24224,
        type=int,
        help="Custom Fluentd port (default: %(default)s) ",
    )
    group.addoption(
        "--fluentd-tag",
        default="test",
        help="Custom Fluentd tag (default: %(default)s)",
    )
    group.addoption(
        "--fluentd-label",
        default="pytest",
        help="Custom Fluentd label (default: %(default)s)",
    )
    group.addoption(
        "--extend-logging",
        action="store_true",
        help="Extend the Python logging with a Fluent handler",
    )


def pytest_configure(config):
    """Extend pytest configuration."""
    global fluent_runtime
    config.fluent = FluentLoggerRuntime(config)
    config.pluginmanager.register(config.fluent, "fluent-reporter-runtime")
    fluent_runtime = config.fluent


def pytest_unconfigure(config):
    """Unregister runtime from pytest."""
    global fluent_runtime
    fluent = getattr(config, "fluent", None)
    if fluent:
        del config.fluent
        config.pluginmanager.unregister(fluent)
        fluent_runtime = None


#####################################################
# Fixtures
#####################################################


@pytest.fixture
def get_logger(request):
    """Create own extended Python logger."""
    config = request.config
    host = config.getoption("--fluentd-host")
    port = config.getoption("--fluentd-port")
    tag = config.getoption("--fluentd-tag")

    def get_logger(name=None):
        logger = logging.getLogger(name)
        if name is None:
            return logger
        add_handler(host, port, tag, logger)
        return logger

    return get_logger


@pytest.fixture
def session_uid() -> typing.Optional[str]:
    """Get the current session UID."""
    return get_session_uid()


@pytest.fixture
def test_uid() -> typing.Optional[str]:
    """Get the current test UID."""
    return get_test_uid()


#####################################################
# functions and classes
#####################################################


# Logging extensions


class RecordFormatter(FluentRecordFormatter):
    """Extension of FluentRecordFormatter in order to add unique ID's"""

    def __init__(self, *args, **kwargs):
        """Specific initilization."""
        super(RecordFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        """Extend formatting for Fluentd handler."""
        data = super(RecordFormatter, self).format(record)

        # Extend record by unique ids.
        data["sessionId"] = get_session_uid()
        data["testId"] = get_test_uid()
        data["stage"] = get_stage()
        return data


def extend_loggers(host, port, tag) -> None:
    """Extend Python logging with a Fluentd handler."""
    modify_logger(host, port, tag, None)
    modify_logger(host, port, tag, "fluent")


def modify_logger(host, port, tag, name=None) -> None:
    """Extend Python logging with a Fluentd handler."""
    logger = logging.getLogger(name)
    add_handler(host, port, tag, logger)


def add_handler(host, port, tag, logger):
    """Add handler to a specific logger."""
    handler = FluentHandler(
        tag, host=host, port=port, buffer_overflow_handler=overflow_handler
    )
    formatter = RecordFormatter(
        {
            "type": "logging",
            "host": "%(hostname)s",
            "where": "%(module)s.%(funcName)s",
            "level": "%(levelname)s",
            "stack_trace": "%(exc_text)s",
        }
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def overflow_handler(pendings):
    """Custom overflow handler."""
    unpacker = msgpack.Unpacker(BytesIO(pendings))
    for unpacked in unpacker:
        print(unpacked)


def set_stage(val: str) -> None:
    """Set the current execution stage."""
    global stage
    stage = val


def get_stage() -> str:
    """Get the current execution stage."""
    return stage


# Unique identifiers


def create_unique_identifier():
    """Create a new unique identifier."""
    return uuid.uuid4()


def get_session_uid() -> typing.Optional[str]:
    """Get current session UID."""
    if fluent_runtime is None:
        return None
    return typing.cast(FluentLoggerRuntime, fluent_runtime).session_uid


def get_test_uid() -> typing.Optional[str]:
    """Get current test UID."""
    if fluent_runtime is None:
        return None
    return typing.cast(FluentLoggerRuntime, fluent_runtime).test_uid
