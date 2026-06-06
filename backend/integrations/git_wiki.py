# MOCKED — replace body of write_wiki_entry() with a real GitHub/GitLab API call
import base64


def build_wiki_entry(ticket, investigation: dict) -> dict:
    """Build a KB markdown entry for the Git wiki."""
    tags = investigation.get("report", "").split("## KB Tags")[-1].strip()
    slug = ticket.id.lower().replace("-", "_")

    content = f"""# [{ticket.id}] {ticket.job_name} failure

**Date**: {ticket.created_at}
**Severity**: {ticket.severity.value if ticket.severity else "unknown"}
**Tags**: {tags}

## Summary
{investigation.get("summary", "")}

## Root Cause
{investigation.get("root_cause", "")}

## Fix
{investigation.get("fix", "")}

## References
- Jenkins build: {ticket.build_url}
- Ticket: {ticket.id}
"""
    return {
        "path":    f"kb/investigations/{slug}.md",
        "message": f"docs(kb): add investigation {ticket.id}",
        "content": content,
    }


async def write_wiki_entry(payload: dict, repo: str, token: str) -> None:
    # MOCK: log payload instead of writing
    import json
    print("[MOCK WIKI]", json.dumps(payload, ensure_ascii=True))
    # Real implementation (GitHub Contents API):
    # import httpx, base64
    # encoded = base64.b64encode(payload["content"].encode()).decode()
    # async with httpx.AsyncClient() as client:
    #     await client.put(
    #         f"https://api.github.com/repos/{repo}/contents/{payload['path']}",
    #         headers={"Authorization": f"Bearer {token}"},
    #         json={"message": payload["message"], "content": encoded},
    #     )
