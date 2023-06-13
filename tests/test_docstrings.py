TEST_DOCSTRING = "This test will always pass."


def test_add_docstrings(run_mocked_pytest, session_uuid):
    runpytest, fluent_sender = run_mocked_pytest
    result = runpytest(
        f"--session-uuid={session_uuid}",
        "--add-docstrings",
        pyfile=f"""
    def test_base():
        '''
        {TEST_DOCSTRING}
        '''
        assert True
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    result.assert_outcomes(passed=1)
    assert len(call_args) > 0
    report = call_args[2].args[2]
    assert "docstring" in report
    assert report.get("docstring") == TEST_DOCSTRING


def test_docstrings_disabled(run_mocked_pytest, session_uuid):
    runpytest, fluent_sender = run_mocked_pytest
    result = runpytest(
        f"--session-uuid={session_uuid}",
        pyfile=f"""
    def test_base():
        '''
        {TEST_DOCSTRING}
        '''
        assert True
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    result.assert_outcomes(passed=1)
    assert len(call_args) > 0
    report = call_args[2].args[2]
    assert "docstring" not in report


def test_missing_docstring(run_mocked_pytest, session_uuid):
    runpytest, fluent_sender = run_mocked_pytest
    result = runpytest(
        f"--session-uuid={session_uuid}",
        "--add-docstrings",
        pyfile="""
    def test_base():
        assert True
    """,
    )
    call_args = fluent_sender.emit_with_time.call_args_list
    result.assert_outcomes(passed=1)
    assert len(call_args) > 0
    report = call_args[2].args[2]
    assert "docstring" not in report
