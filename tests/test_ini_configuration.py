import socket

TAG = "unittest"
LABEL = "pytest"
PORT = 12345


def test_commandline_args(pytester, session_uuid):

    filename = make_py_file(pytester, tag=TAG, logging=True)
    print(filename)
    result = pytester.runpytest("--extend-logging", f"--fluentd-tag={TAG}")
    """result.stdout.fnmatch_lines(
        [
            "*::test_fluentd_config PASSED*",
        ]
    )"""
    assert result.ret == 0


def test_tox_ini_setting(pytester, session_uuid):

    pytester.makeini(
        f"[pytest]\naddopts = --session-uuid='{session_uuid}' --fluentd-port={PORT} --fluentd-host=localhost --fluentd-tag='{TAG}' --fluentd-label='{LABEL}' --extend-logging"
    )

    make_py_file(pytester, session_uuid, TAG, LABEL, PORT, "localhost", True)

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_fluentd_config PASSED*",
        ]
    )
    assert result.ret == 0


def test_pyprojtoml_ini_setting(pytester, session_uuid):

    pytester.makepyprojecttoml(
        f"[tool.pytest.ini_options]\naddopts = \"--session-uuid='{session_uuid}' --fluentd-port={PORT} --fluentd-host=localhost --fluentd-tag='{TAG}' --extend-logging\""
    )

    make_py_file(pytester, session_uuid, TAG, LABEL, PORT, "localhost", True)

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_fluentd_config PASSED*",
        ]
    )
    assert result.ret == 0


def test_pytest_ini_setting(pytester, session_uuid):
    pytester.makefile(
        ".ini",
        pytest=f"[pytest]\naddopts = --session-uuid='{session_uuid}' --fluentd-port={PORT} --fluentd-host=localhost --fluentd-tag='{TAG}' --fluentd-label='{LABEL}' --extend-logging",
    )

    make_py_file(pytester, session_uuid, TAG, LABEL, PORT, "localhost", True)

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_fluentd_config PASSED*",
        ]
    )
    assert result.ret == 0


def make_py_file(
    pytester,
    session_uuid="",
    tag="test",
    label="pytest",
    port=24224,
    host=socket.gethostname(),
    logging=False,
):

    session_uuid_str = (
        f'assert pytest_config.getoption("--session-uuid") == "{session_uuid}"'
    )

    tag_str = f'assert pytest_config.getoption("--fluentd-tag") == "{tag}"'

    label_str = (
        f'assert pytest_config.getoption("--fluentd-label") == "{label}"'
    )

    port_str = f'assert pytest_config.getoption("--fluentd-port") == {port}'

    host_str = f'assert pytest_config.getoption("--fluentd-host") == "{host}"'

    log_str = (
        f'assert pytest_config.getoption("--extend-logging") == {logging}'
    )

    return pytester.makepyfile(
        f"""
            import pytest

            @pytest.fixture
            def pytest_config(request):
                return request.config

            def test_fluentd_config(pytest_config):
                {session_uuid_str if session_uuid else session_uuid}
                {host_str}
                {port_str}
                {tag_str}
                {label_str}
                {log_str}
            """
    )
