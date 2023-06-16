def test_get_logger(run_mocked_pytest, session_uuid, logging_content):
    runpytest, fluent_sender = run_mocked_pytest
    result = runpytest(
        f"--session-uuid={session_uuid}",
        "--extend-logging",
        pyfile=f"""
    def test_base(get_logger):
        LOGGER = get_logger('my.Logger')
        LOGGER.info('{logging_content}')
        assert True
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    result.assert_outcomes(passed=1)
    assert len(call_args) > 0
    for idx, call_arg in enumerate(call_args):
        data = call_arg.args[2]
        if idx in [2, 3]:
            assert data.get("type") == "logging"
            assert "host" in data
            assert "where" in data
            assert "level" in data
            assert "stack_trace" in data
            assert data.get("message") == logging_content


def test_uid_fixtures(run_mocked_pytest, session_uuid):
    runpytest, _ = run_mocked_pytest
    result = runpytest(
        f"--session-uuid={session_uuid}",
        pyfile="""
    from pytest_fluent import get_session_uid, get_test_uid

    def test_base(session_uid, test_uid):
        assert session_uid == get_session_uid()
        assert test_uid == get_test_uid()
    """,
    )
    result.assert_outcomes(passed=1)
