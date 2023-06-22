import logging
import socket

import pytest

# set log_level="DEBUG" and log_cli = true in pyproject.toml configuration when
# debug info is needed
logger = logging.getLogger("debug-log")

TAG = "unittest"
LABEL = "pytest"
PORT = 12345
HOSTNAME = socket.gethostname()


@pytest.fixture
def tox_ini(pytester, session_uuid):
    return pytester.makeini(
        f'[pytest]\naddopts = --session-uuid="{session_uuid}" --fluentd-port={PORT} '
        f'--fluentd-host="{HOSTNAME}" --fluentd-tag="{TAG}" --fluentd-label="{LABEL}" '
        f"--extend-logging"
    )


@pytest.fixture
def pyprojtoml_ini(pytester, session_uuid):
    return pytester.makepyprojecttoml(
        f'[tool.pytest.ini_options]\naddopts = "--session-uuid={session_uuid} '
        f"--fluentd-port={PORT} --fluentd-host={HOSTNAME} --fluentd-tag={TAG} "
        f'--extend-logging"'
    )


@pytest.fixture
def pytest_ini(pytester, session_uuid):
    return pytester.makefile(
        ".ini",
        pytest=f'[pytest]\naddopts = --session-uuid="{session_uuid}" '
        f'--fluentd-port={PORT} --fluentd-host="{HOSTNAME}" --fluentd-tag="{TAG}" '
        f'--fluentd-label="{LABEL}" --extend-logging',
    )


@pytest.mark.parametrize("ini_path", ["tox_ini", "pyprojtoml_ini", "pytest_ini"])
def test_ini_setting(pytester, run_mocked_pytest, session_uuid, ini_path, request):
    runpytest, _ = run_mocked_pytest
    ini_file = request.getfixturevalue(ini_path)
    logger.debug("Generated ini file: %s", ini_file)

    filename = make_py_file(pytester, session_uuid, TAG, LABEL, PORT, HOSTNAME, True)
    logger.debug("Generated python module: %s", filename)
    result = runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*passed*",
        ]
    )
    assert result.ret == 0


@pytest.mark.parametrize("ini_path", ["tox_ini", "pyprojtoml_ini", "pytest_ini"])
def test_cli_args_precedence(pytester, run_mocked_pytest, ini_path, request):
    runpytest, _ = run_mocked_pytest
    fluent_tag = "dummytest"
    fluent_label = "pytester"
    fluent_port = 65535

    ini_file = request.getfixturevalue(ini_path)
    logger.debug("Generated ini file: %s", ini_file)

    filename = make_py_file(
        pytester, tag=fluent_tag, label=fluent_label, port=fluent_port, is_logging=True
    )
    logger.debug("Generated python module: %s", filename)
    result = runpytest(
        f"--fluentd-tag={fluent_tag}",
        f"--fluentd-label={fluent_label}",
        f"--fluentd-port={fluent_port}",
    )
    result.stdout.fnmatch_lines(
        [
            "*passed*",
        ]
    )
    assert result.ret == 0


def test_commandline_args(pytester, run_mocked_pytest):
    runpytest, _ = run_mocked_pytest
    filename = make_py_file(pytester, tag=TAG, is_logging=True)
    logger.debug("Generated python module: %s", filename)
    result = runpytest("--extend-logging", f"--fluentd-tag={TAG}")
    result.stdout.fnmatch_lines(
        [
            "*passed*",
        ]
    )
    assert result.ret == 0


def make_py_file(
    pytester,
    session_id="",
    tag="test",
    label="pytest",
    port=24224,
    host="",
    is_logging=False,
):
    session_id_str = (
        f'assert pytest_config.getoption("--session-uuid") == "{session_id}"'
    )

    tag_str = f'assert pytest_config.getoption("--fluentd-tag") == "{tag}"'

    label_str = f'assert pytest_config.getoption("--fluentd-label") == "{label}"'

    port_str = f'assert pytest_config.getoption("--fluentd-port") == {port}'

    host_str = f'assert pytest_config.getoption("--fluentd-host") == "{host}"'

    log_str = f'assert pytest_config.getoption("--extend-logging") == {is_logging}'

    return pytester.makepyfile(
        f"""
            import pytest

            @pytest.fixture
            def pytest_config(request):
                return request.config

            def test_fluentd_config(pytest_config):
                {session_id_str if session_id else session_id}
                {host_str if host else host}
                {port_str}
                {tag_str}
                {label_str}
                {log_str}
            """
    )
