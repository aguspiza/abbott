from pathlib import Path
from .models import Ticket, Severity
from .config import settings

SYSTEM_PROMPT = Path(__file__).parent.parent / "prompts" / "investigate.md"


def investigate(ticket: Ticket) -> dict:
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

    text = _call_llm(system, user_msg)

    return {
        "report":     text,
        "severity":   _extract_severity(text),
        "summary":    _extract_section(text, "## Summary"),
        "root_cause": _extract_section(text, "## Root Cause"),
        "fix":        _extract_section(text, "## Fix"),
    }


def _call_llm(system: str, user_msg: str) -> str:
    if settings.anthropic_api_key:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return response.content[0].text
    else:
        from openai import OpenAI
        client = OpenAI(base_url=settings.openai_base_url, api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_msg},
            ],
        )
        return response.choices[0].message.content


def _extract_severity(text: str) -> Severity:
    section = _extract_section(text, "## Severity").lower()
    if section:
        if "bug" in section:
            return Severity.BUG
        if "flaky" in section:
            return Severity.FLAKY
        if "warning" in section:
            return Severity.WARNING
    t = text.lower()
    if "regression" in t:
        return Severity.BUG
    if "transient" in t:
        return Severity.FLAKY
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
