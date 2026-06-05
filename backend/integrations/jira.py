# MOCKED — replace body of create_jira_issue() with a real httpx.post call


def build_jira_payload(ticket, investigation: dict) -> dict:
    """Build Jira issue create payload (REST API v3 format)."""
    return {
        "fields": {
            "project":     {"key": "OPS"},
            "summary":     f"[CI] Pipeline failure: {ticket.job_name}",
            "description": {
                "type":    "doc",
                "version": 1,
                "content": [{
                    "type":    "paragraph",
                    "content": [{"type": "text", "text": investigation.get("report", "")}],
                }],
            },
            "issuetype": {"name": "Bug"},
            "priority":  {"name": "High"},
            "labels":    ["jenkins", "automated"],
            "customfield_build_url":  ticket.build_url,
            "customfield_ticket_id":  ticket.id,
        }
    }


async def create_jira_issue(payload: dict, jira_base_url: str, token: str) -> None:
    # MOCK: log payload instead of sending
    print("[MOCK JIRA]", payload)
    # Real implementation:
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     await client.post(
    #         f"{jira_base_url}/rest/api/3/issue",
    #         headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    #         json=payload,
    #     )
