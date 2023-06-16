def test_data_reporter_base_with_passed(run_mocked_pytest, session_uuid):
    runpytest, fluent_sender = run_mocked_pytest
    result = runpytest(
        f"--session-uuid={session_uuid}",
        pyfile="""
    def test_base():
        assert True
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    result.assert_outcomes(passed=1)
    assert len(call_args) > 0
    report = call_args[2].args[2]
    assert report.get("name") == "test_data_reporter_base_with_passed.py::test_base"
    assert report.get("outcome") == "passed"
    assert "duration" in report
    markers = report.get("markers")
    assert markers.get("test_base") == 1
    assert markers.get("test_data_reporter_base_with_passed.py") == 1
    assert markers.get("test_data_reporter_base_with_passed0") == 1
    assert report.get("sessionId") == str(session_uuid)
    assert "testId" in report


def test_data_reporter_xdist_passed(run_mocked_pytest, session_uuid):
    runpytest, fluent_sender = run_mocked_pytest
    result = runpytest(
        "-n 2",
        f"--session-uuid={session_uuid}",
        pyfile="""
    def test_base_group_one():
        assert True

    def test_base_group_two():
        assert True

    def test_base_group_three():
        assert True

    def test_base_group_four():
        assert True

    def test_base_group_five():
        assert True

    def test_base_group_six():
        assert True
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    result.assert_outcomes(passed=6)
    assert len(call_args) > 0
    check_for_verdicts(session_uuid, call_args)


def check_for_verdicts(session_uuid, call_args):
    for call_arg in call_args:
        args = call_arg.args[2]
        if args.get("report") == "call":
            check_for_verdict(session_uuid, args)


def check_for_verdict(session_uuid, report: dict):
    assert "name" in report
    name = report["name"].split("::")[1]
    assert report.get("outcome") == "passed"
    assert "duration" in report
    markers = report.get("markers")
    assert markers.get(name) == 1
    assert markers.get("test_data_reporter_xdist_passed.py") == 1
    assert markers.get("test_data_reporter_xdist_passed0") == 1
    assert report.get("sessionId") == str(session_uuid)
    assert "testId" in report


def test_data_reporter_base_with_xfail(run_mocked_pytest, session_uuid):
    runpytest, fluent_sender = run_mocked_pytest
    _ = runpytest(
        f"--session-uuid={session_uuid}",
        pyfile="""
    import pytest

    @pytest.mark.xfail
    def test_base():
        assert False
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    assert len(call_args) > 0
    args = call_args[2].args[2]
    assert args.get("outcome") == "xfailed"
    assert "failure_message" in args
    assert args.get("markers", {}).get("xfail") == 1


def test_data_reporter_base_with_exception(run_mocked_pytest, session_uuid):
    runpytest, fluent_sender = run_mocked_pytest
    _ = runpytest(
        f"--session-uuid={session_uuid}",
        pyfile="""
    def test_base():
        raise Exception('TestException')
        assert True
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    assert len(call_args) > 0
    args = call_args[2].args[2]
    assert args.get("when") == "call"
    assert args.get("outcome") == "error"
    assert "failure_message" in args


def test_data_reporter_base_with_setup_exception(run_mocked_pytest, session_uuid):
    runpytest, fluent_sender = run_mocked_pytest
    _ = runpytest(
        f"--session-uuid={session_uuid}",
        pyfile="""
    import pytest

    @pytest.fixture
    def my_value() -> str:
        val = '1'
        raise ValueError('Value is wrong')
        return val

    def test_base(my_value):
        raise Exception('TestException')
        assert True
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    assert len(call_args) > 0
    args = call_args[2].args[2]
    assert args.get("when") == "setup"
    assert args.get("outcome") == "error"
    assert "failure_message" in args
