from .models import Ticket, TicketStatus
from .parser import parse_log
from .investigator import investigate
from .integrations.teams import build_teams_payload, send_teams
from .integrations.jira import build_jira_payload, create_jira_issue
from .integrations.git_wiki import build_wiki_entry, write_wiki_entry
from .config import settings


async def process_ticket(ticket: Ticket, db) -> None:
    """Full investigation pipeline for a single ticket."""
    try:
        # 1. Parse log
        ticket.parsed = parse_log(ticket.raw_log)
        ticket.status = TicketStatus.INVESTIGATING
        await db.save(ticket)

        # 2. Investigate with Claude
        result = investigate(ticket)
        ticket.severity      = result["severity"]
        ticket.investigation = result["report"]

        # 3. Build + store mock payloads
        teams_payload = build_teams_payload(ticket, result)
        ticket.teams_payload = teams_payload

        wiki_payload = build_wiki_entry(ticket, result)
        ticket.wiki_payload = wiki_payload

        if ticket.severity == "bug":
            jira_payload = build_jira_payload(ticket, result)
            ticket.jira_payload = jira_payload
            # await create_jira_issue(jira_payload, settings.JIRA_URL, settings.JIRA_TOKEN)

        # 4. Send outputs (mocked — uncomment real calls when ready)
        await send_teams(teams_payload, settings.TEAMS_WEBHOOK)
        await write_wiki_entry(wiki_payload, settings.WIKI_REPO, settings.GITHUB_TOKEN)

        ticket.status = TicketStatus.RESOLVED

    except Exception as exc:
        ticket.status      = TicketStatus.FAILED
        ticket.investigation = f"Worker error: {exc}"

    await db.save(ticket)
