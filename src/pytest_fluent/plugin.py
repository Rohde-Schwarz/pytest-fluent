"""pytest-fluent-logging plugin definition."""
import datetime
import logging
import os
import textwrap
import time
import typing
import uuid
from io import BytesIO

import msgpack
import pytest
from fluent.handler import FluentHandler, FluentRecordFormatter

from .additional_information import get_additional_information_callback
from .content_patcher import ContentPatcher
from .event import Event
from .setting_file_loader_action import (
    SettingFileLoaderAction,
    load_and_check_settings_file,
)
from .test_report import LogReport

#####################################################
# Plugin runtime
#####################################################

DOCSTRING_KEY = "docstring"
DOCSTRING_STASHKEY = pytest.StashKey[str]()


class FluentLoggerRuntime(object):
    def __init__(self, config):
        self._session_uuid = None
        self._session_start_time = None
        self._test_uuid = None
        self.config = config
        self._set_session_uid(self.config.getoption("--session-uuid"))
        self._host = config.getoption("--fluentd-host")
        self._port = config.getoption("--fluentd-port")
        self._tag = config.getoption("--fluentd-tag")
        self._label = config.getoption("--fluentd-label")
        self._timestamp = config.getoption("--fluentd-timestamp")
        self._extend_logging = config.getoption("--extend-logging")
        self._add_docstrings = config.getoption("--add-docstrings")
        stage_names = [method for method in dir(self) if method.startswith("pytest_")]
        stage_names.append("logging")
        self._content_patcher = ContentPatcher(
            user_settings=config.getoption("--stage-settings"),
            args_settings=config.option,
            stage_names=stage_names,
        )
        tags: typing.List[str] = []
        for value in self._content_patcher.user_settings.values():
            tag = value.get("tag")
            if not tag:
                continue
            tags.append(tag)
        tags = list(set(tags))
        self._event = Event(
            tags, self._host, self._port, buffer_overflow_handler=overflow_handler
        )
        self._log_reporter = LogReport(self.config)
        self._patch_logging()

    def _patch_logging(self):
        if not self._extend_logging:
            return
        tag = self._content_patcher.user_settings.get("logging", {}).get("tag")
        if not tag:
            raise ValueError(
                "Tag for logging was not set. Please set either specific tag value for \
                    key 'logging' or use the 'all' object in stage settings file."
            )
        label = self._content_patcher.user_settings.get("logging", {}).get("label")
        if label:
            tag = f"{tag}.{label}"
        extend_loggers(
            self._host,
            self._port,
            tag,
            self._content_patcher,
        )

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

    def _set_timestamp_information(self, data: dict):
        if self._timestamp is not None:
            data.update({self._timestamp: f"{datetime.datetime.utcnow().isoformat()}"})

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
        self._session_start_time = time.time()
        if not self.config.getoption("collectonly"):
            data = {
                "status": "start",
                "stage": "session",
                "sessionId": self.session_uid,
            }
            data = self._content_patcher.patch(data)
            data.update(get_additional_information_callback())
            self._set_timestamp_information(data=data)
            tag, label = self._content_patcher.get_tag_and_label()
            self._event(tag, label, data)

    def pytest_runtest_logstart(self, nodeid: str, location: typing.Tuple[int, str]):
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
            data = self._content_patcher.patch(data)
            data.update(get_additional_information_callback())
            self._set_timestamp_information(data=data)
            tag, label = self._content_patcher.get_tag_and_label()
            self._event(tag, label, data)

    def pytest_runtest_setup(self, item: pytest.Item):
        """Custom hook for test setup."""
        set_stage("testcase")
        docstring = get_test_docstring(item)
        item.stash[DOCSTRING_STASHKEY] = docstring
        if not self.config.getoption("collectonly"):
            pass

    def pytest_runtest_teardown(self, item: pytest.Item, nextitem: pytest.Item):
        """Custom hook for test teardown."""
        set_stage("testcase")
        docstring = get_test_docstring(item)
        item.stash[DOCSTRING_STASHKEY] = docstring
        if not self.config.getoption("collectonly"):
            pass

    def pytest_runtest_call(self, item: pytest.Item):
        """Custom hook for test call."""
        set_stage("testcase")
        if not self.config.getoption("collectonly"):
            pass

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Item, call):
        """Custom hook for make report."""
        report = (yield).get_result()
        docstring = item.stash.get(DOCSTRING_STASHKEY, None)
        report.stash = {DOCSTRING_KEY: docstring}

    def pytest_runtest_logreport(self, report: pytest.TestReport):
        """Custom hook for logging results."""
        set_stage("testcase")
        if not self.config.getoption("collectonly"):
            data = self._log_reporter(report)
            if not data:
                return
            data.update(
                {
                    "stage": "testcase",
                    "when": report.when,
                    "sessionId": self.session_uid,
                    "testId": self.test_uid,
                }
            )
            if self._add_docstrings:
                docstring = report.stash.get(DOCSTRING_KEY, None)
                if docstring:
                    data.update({"docstring": docstring})
            self._set_timestamp_information(data=data)
            data = self._content_patcher.patch(data)
            data.update(get_additional_information_callback())
            tag, label = self._content_patcher.get_tag_and_label()
            self._event(tag, label, data)

    def pytest_runtest_logfinish(
        self,
        nodeid: str,
        location: typing.Tuple[str, typing.Optional[int], str],
    ):
        """Custom hook for test end."""
        set_stage("testcase")
        if not self.config.getoption("collectonly"):
            data = {
                "status": "finish",
                "stage": "testcase",
                "sessionId": self.session_uid,
                "testId": self.test_uid,
                "name": nodeid,
            }
            self._set_timestamp_information(data=data)
            data = self._content_patcher.patch(data)
            data.update(get_additional_information_callback())
            tag, label = self._content_patcher.get_tag_and_label()
            self._event(tag, label, data)

    def pytest_sessionfinish(
        self,
        session: pytest.Session,
        exitstatus: typing.Union[int, pytest.ExitCode],
    ):
        """Custom hook for session end."""
        set_stage("session")
        if not self.config.getoption("collectonly"):
            data = {
                "status": "finish",
                "duration": (
                    time.time()
                    - (
                        0
                        if self._session_start_time is None
                        else self._session_start_time
                    )
                ),
                "stage": "session",
                "sessionId": self.session_uid,
            }
            self._set_timestamp_information(data=data)
            data = self._content_patcher.patch(data)
            data.update(get_additional_information_callback())
            tag, label = self._content_patcher.get_tag_and_label()
            self._event(tag, label, data)


STAGE: str = "session"
FLUENT_RUNTIME: typing.Optional[FluentLoggerRuntime] = None

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
        default="localhost",
        type=str,
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
        "--fluentd-timestamp",
        default=None,
        help="Custom Fluentd timestamp (default: %(default)s)",
    )
    group.addoption(
        "--extend-logging",
        action="store_true",
        help="Extend the Python logging with a Fluent handler",
    )
    group.addoption(
        "--add-docstrings",
        action="store_true",
        help="Add test docstrings to the testcase call messages.",
    )
    group.addoption(
        "--stage-settings",
        type=str,
        default=load_and_check_settings_file(
            os.path.join(os.path.dirname(__file__), "data", "default.stage.json")
        ),
        action=SettingFileLoaderAction,
        help="Stage setting description JSON or YAML file path or string object.",
    )


def pytest_configure(config):
    """Extend pytest configuration."""
    global FLUENT_RUNTIME
    config.fluent = FluentLoggerRuntime(config)
    config.pluginmanager.register(config.fluent, "fluent-reporter-runtime")
    FLUENT_RUNTIME = config.fluent


def pytest_unconfigure(config):
    """Unregister runtime from pytest."""
    global FLUENT_RUNTIME
    fluent = getattr(config, "fluent", None)
    if fluent:
        del config.fluent
        config.pluginmanager.unregister(fluent)
        FLUENT_RUNTIME = None


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

    def get_logger_wrapper(name=None):
        logger = logging.getLogger(name)
        if name is None:
            return logger
        add_handler(host, port, tag, logger)
        return logger

    return get_logger_wrapper


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

    def __init__(self, patcher: typing.Optional[ContentPatcher], *args, **kwargs):
        """Specific initilization."""
        super(RecordFormatter, self).__init__(*args, **kwargs)
        self.content_patcher = patcher

    def format(self, record):
        """Extend formatting for Fluentd handler."""
        data = super(RecordFormatter, self).format(record)

        # Extend record by unique ids.
        data["sessionId"] = get_session_uid()
        data["testId"] = get_test_uid()
        data["stage"] = get_stage()
        if self.content_patcher:
            data = self.content_patcher.patch(data, "logging", ["tag", "label"])
        return data


def extend_loggers(host, port, tag, patcher: ContentPatcher) -> None:
    """Extend Python logging with a Fluentd handler."""
    modify_logger(host, port, tag, None, patcher)
    modify_logger(host, port, tag, "fluent", patcher)


def modify_logger(
    host, port, tag, name=None, patcher: typing.Optional[ContentPatcher] = None
) -> None:
    """Extend Python logging with a Fluentd handler."""
    logger = logging.getLogger(name)
    add_handler(host, port, tag, logger, patcher)


def add_handler(
    host, port, tag, logger, patcher: typing.Optional[ContentPatcher] = None
):
    """Add handler to a specific logger."""
    handler = FluentHandler(
        tag, host=host, port=port, buffer_overflow_handler=overflow_handler
    )
    formatter = RecordFormatter(
        patcher,
        {
            "type": "logging",
            "host": "%(hostname)s",
            "where": "%(module)s.%(funcName)s",
            "level": "%(levelname)s",
            "stack_trace": "%(exc_text)s",
        },
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
    global STAGE
    STAGE = val


def get_stage() -> str:
    """Get the current execution stage."""
    return STAGE


# Unique identifiers


def create_unique_identifier():
    """Create a new unique identifier."""
    return uuid.uuid4()


def get_session_uid() -> typing.Optional[str]:
    """Get current session UID."""
    if FLUENT_RUNTIME is None:
        return None
    return typing.cast(FluentLoggerRuntime, FLUENT_RUNTIME).session_uid


def get_test_uid() -> typing.Optional[str]:
    """Get current test UID."""
    if FLUENT_RUNTIME is None:
        return None
    return typing.cast(FluentLoggerRuntime, FLUENT_RUNTIME).test_uid


# Docstrings


def get_test_docstring(item: pytest.Item) -> typing.Optional[str]:
    """Extract the docstring from a pytest test item."""
    if hasattr(item, "obj") and item.obj.__doc__ is not None:
        doc = textwrap.dedent(item.obj.__doc__)
        # Remove heading and trailing newlines
        doc = doc.lstrip("\n").rstrip("\n")
        return doc
    return None
