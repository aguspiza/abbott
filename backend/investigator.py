import anthropic
from pathlib import Path
from .models import Ticket, Severity

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

SYSTEM_PROMPT = Path(__file__).parent.parent / "prompts" / "investigate.md"


def investigate(ticket: Ticket) -> dict:
    """
    Call Claude to investigate a parsed Jenkins failure.
    Returns structured investigation result.
    """
    system = SYSTEM_PROMPT.read_text()
    parsed = ticket.parsed or {}

    user_msg = f"""## Jenkins Failure Report

**Job**: {ticket.job_name or "unknown"}
**Build URL**: {ticket.build_url or "unknown"}
**Parsed fields**: {parsed}

## Log tail (last 80 lines)
```
{parsed.get("tail", ticket.raw_log[-3000:])}
```
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text

    return {
        "report":     text,
        "severity":   _extract_severity(text),
        "summary":    _extract_section(text, "## Summary"),
        "root_cause": _extract_section(text, "## Root Cause"),
        "fix":        _extract_section(text, "## Fix"),
    }


def _extract_severity(text: str) -> Severity:
    t = text.lower()
    if "severity: bug" in t or "regression" in t:
        return Severity.BUG
    if "severity: flaky" in t or "transient" in t:
        return Severity.FLAKY
    if "severity: warning" in t:
        return Severity.WARNING
    return Severity.UNKNOWN


def _extract_section(text: str, header: str) -> str:
    lines = text.splitlines()
    capture, out = False, []
    for line in lines:
        if line.strip().startswith(header):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            out.append(line)
    return "\n".join(out).strip()
