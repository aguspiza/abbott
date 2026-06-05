# MOCKED — replace body of send_teams() with a real httpx.post call


def build_teams_payload(ticket, investigation: dict) -> dict:
    """Build Microsoft Teams Adaptive Card payload."""
    return {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "size": "Large",
                        "weight": "Bolder",
                        "text": f"🔴 Pipeline Failure — {ticket.job_name}",
                    },
                    {
                        "type": "TextBlock",
                        "wrap": True,
                        "text": investigation.get("summary", ""),
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {"title": "Severity",   "value": str(ticket.severity)},
                            {"title": "Ticket",     "value": ticket.id},
                            {"title": "Root Cause", "value": investigation.get("root_cause", "")[:200]},
                        ],
                    },
                    {
                        "type": "ActionSet",
                        "actions": [
                            {"type": "Action.OpenUrl", "title": "View Ticket",
                             "url": f"http://your-app/tickets/{ticket.id}"},
                            {"type": "Action.OpenUrl", "title": "Jenkins Build",
                             "url": ticket.build_url or "#"},
                        ],
                    },
                ],
            },
        }],
    }


async def send_teams(payload: dict, webhook_url: str) -> None:
    # MOCK: log payload instead of sending
    print("[MOCK TEAMS]", payload)
    # Real implementation:
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     await client.post(webhook_url, json=payload)
