import asyncio
from .models import Ticket, TicketStatus
from .parser import parse_log
from .investigator import investigate
from .integrations.teams import build_teams_payload, send_teams
from .integrations.jira import build_jira_payload
from .integrations.git_wiki import build_wiki_entry, write_wiki_entry
from .config import settings


async def process_ticket(ticket: Ticket, db) -> None:
    try:
        ticket.parsed = parse_log(ticket.raw_log)
        ticket.status = TicketStatus.INVESTIGATING
        await db.save(ticket)

        result = await asyncio.to_thread(investigate, ticket)
        ticket.severity      = result["severity"]
        ticket.investigation = result["report"]

        teams_payload = build_teams_payload(ticket, result)
        ticket.teams_payload = teams_payload
        await send_teams(teams_payload, settings.teams_webhook)

        if ticket.severity.value == "bug":
            jira_payload = build_jira_payload(ticket, result)
            ticket.jira_payload = jira_payload

            wiki_payload = build_wiki_entry(ticket, result)
            ticket.wiki_payload = wiki_payload
            await write_wiki_entry(wiki_payload, settings.wiki_repo, settings.github_token)

        ticket.status = TicketStatus.RESOLVED

    except Exception as exc:
        ticket.status = TicketStatus.FAILED
        ticket.investigation = f"Worker error: {exc}"

    await db.save(ticket)


async def analysis_loop(db_factory, concurrency: int, poll_interval: int) -> None:
    """
    Polls for OPEN tickets every poll_interval seconds and processes up to
    concurrency tickets simultaneously. Tasks are picked oldest-first (FIFO).
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def run_one(ticket, db):
        async with semaphore:
            await process_ticket(ticket, db)

    while True:
        await asyncio.sleep(poll_interval)
        try:
            db = await db_factory()
            tickets = await db.list(days=0)
            open_tickets = [t for t in tickets if t.status == TicketStatus.OPEN]
            for ticket in reversed(open_tickets):  # reversed = oldest first
                asyncio.create_task(run_one(ticket, db))
        except Exception as exc:
            print(f"[analysis_loop] {exc}")
