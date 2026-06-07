from backend.parser import parse_log


def test_detects_exit_code():
    result = parse_log("Process exited with code 1\nERROR: Build failed")
    assert result["exit_code"] == "1"
    assert result["error_line"] == "Build failed"


def test_detects_exception_marks_bug():
    result = parse_log("java.lang.NullPointerException: null reference")
    assert "NullPointerException" in result["exception"]
    assert result["hint_severity"] == "bug"


def test_detects_oom_marks_bug():
    result = parse_log("FATAL: OutOfMemoryError: Java heap space")
    assert result["oom"]
    assert result["hint_severity"] == "bug"


def test_detects_timeout_marks_flaky():
    result = parse_log("Build timed out after 10 minutes")
    assert result.get("timeout")
    assert result["hint_severity"] == "flaky"


def test_detects_test_failures_marks_bug():
    result = parse_log("Tests run: 10, Failures: 2, Errors: 1")
    assert result["test_fail"] == "2"
    assert result["hint_severity"] == "bug"


def test_tail_truncates_to_80_lines():
    lines = [f"line {i}" for i in range(100)]
    result = parse_log("\n".join(lines))
    assert result["total_lines"] == 100
    assert len(result["tail"].splitlines()) == 80


def test_empty_log_returns_unknown():
    result = parse_log("")
    assert result["total_lines"] == 0
    assert result["hint_severity"] == "unknown"


def test_no_match_returns_unknown():
    result = parse_log("Everything is fine, deployment complete.")
    assert result["hint_severity"] == "unknown"
    assert "exit_code" not in result
