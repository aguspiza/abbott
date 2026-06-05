import re
from typing import Optional

# Patterns to extract signal from Jenkins logs
PATTERNS = {
    "exit_code":  r"Process exited with code (\d+)",
    "stage":      r"\[Pipeline\] stage\s*\n\[Pipeline\] \{ \((.+?)\)",
    "exception":  r"([\w\.]+Exception[^\n]*)",
    "error_line": r"ERROR: (.+)",
    "oom":        r"(OutOfMemoryError|Cannot allocate memory|OOMKilled)",
    "timeout":    r"(Timeout|timed out|deadline exceeded)",
    "test_fail":  r"Tests run: \d+, Failures: (\d+), Errors: (\d+)",
    "docker_err": r"(docker: Error|manifest unknown|denied: access forbidden)",
}


def parse_log(raw_log: str) -> dict:
    """Extract structured fields from a raw Jenkins log."""
    result: dict = {}
    for key, pattern in PATTERNS.items():
        match = re.search(pattern, raw_log, re.IGNORECASE | re.MULTILINE)
        if match:
            result[key] = match.group(1) if match.lastindex else match.group(0)

    # Heuristic severity pre-classification (AI will refine)
    if result.get("oom") or result.get("exception"):
        result["hint_severity"] = "bug"
    elif result.get("timeout"):
        result["hint_severity"] = "flaky"
    elif result.get("test_fail"):
        result["hint_severity"] = "bug"
    else:
        result["hint_severity"] = "unknown"

    # Truncate log to last N lines for prompt (avoid token explosion)
    lines = raw_log.strip().splitlines()
    result["tail"] = "\n".join(lines[-80:])
    result["total_lines"] = len(lines)

    return result
