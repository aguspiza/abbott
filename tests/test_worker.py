import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.models import Severity, Ticket, TicketStatus
from backend.worker import analysis_loop, process_ticket


def _ticket(**kwargs) -> Ticket:
    defaults: dict = dict(
        id="TKT-TEST0001",
        job_name="test-job",
        build_url=None,
        raw_log="Process exited with code 1\nERROR: Build failed",
        status=TicketStatus.OPEN,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return Ticket(**defaults)


_FAKE_RESULT = {
    "severity": Severity.BUG,
    "report": "## Summary\nBuild failed.\n\n## Severity\nbug",
    "raw": "",
}


async def test_process_ticket_resolves_on_success():
    ticket = _ticket()
    db = AsyncMock()

    with (
        patch("backend.worker.investigate", return_value=_FAKE_RESULT),
        patch("backend.worker.build_teams_payload", return_value={"type": "message"}),
        patch("backend.worker.send_teams", new_callable=AsyncMock),
        patch("backend.worker.build_jira_payload", return_value={"fields": {}}),
        patch("backend.worker.build_wiki_entry", return_value={"content": ""}),
        patch("backend.worker.write_wiki_entry", new_callable=AsyncMock),
    ):
        await process_ticket(ticket, db)

    assert ticket.status == TicketStatus.RESOLVED
    assert ticket.severity == Severity.BUG
    assert ticket.investigation == _FAKE_RESULT["report"]


async def test_process_ticket_saves_twice():
    ticket = _ticket()
    db = AsyncMock()

    with (
        patch("backend.worker.investigate", return_value=_FAKE_RESULT),
        patch("backend.worker.build_teams_payload", return_value={}),
        patch("backend.worker.send_teams", new_callable=AsyncMock),
        patch("backend.worker.build_jira_payload", return_value={}),
        patch("backend.worker.build_wiki_entry", return_value={}),
        patch("backend.worker.write_wiki_entry", new_callable=AsyncMock),
    ):
        await process_ticket(ticket, db)

    assert db.save.call_count == 2  # once for INVESTIGATING, once for RESOLVED


async def test_process_ticket_marks_failed_on_error():
    ticket = _ticket()
    db = AsyncMock()

    with patch("backend.worker.investigate", side_effect=RuntimeError("LLM down")):
        await process_ticket(ticket, db)

    assert ticket.status == TicketStatus.FAILED
    assert "LLM down" in ticket.investigation


async def test_process_ticket_skips_jira_for_non_bug():
    ticket = _ticket()
    db = AsyncMock()
    non_bug_result = {**_FAKE_RESULT, "severity": Severity.FLAKY}

    with (
        patch("backend.worker.investigate", return_value=non_bug_result),
        patch("backend.worker.build_teams_payload", return_value={}),
        patch("backend.worker.send_teams", new_callable=AsyncMock),
        patch("backend.worker.build_jira_payload") as mock_jira,
        patch("backend.worker.build_wiki_entry") as mock_wiki,
        patch("backend.worker.write_wiki_entry", new_callable=AsyncMock) as mock_write,
    ):
        await process_ticket(ticket, db)

    mock_jira.assert_not_called()
    mock_wiki.assert_not_called()
    mock_write.assert_not_called()


async def test_analysis_loop_picks_up_open_tickets():
    ticket = _ticket()
    db = AsyncMock()
    db.list.return_value = [ticket]
    db_factory = AsyncMock(return_value=db)

    processed: list[str] = []

    async def fake_process(t, d):
        processed.append(t.id)

    with patch("backend.worker.process_ticket", side_effect=fake_process):
        task = asyncio.create_task(analysis_loop(db_factory, concurrency=2, poll_interval=0))
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    assert ticket.id in processed


async def test_analysis_loop_ignores_non_open_tickets():
    resolved = _ticket(status=TicketStatus.RESOLVED)
    db = AsyncMock()
    db.list.return_value = [resolved]
    db_factory = AsyncMock(return_value=db)

    processed: list[str] = []

    async def fake_process(t, d):
        processed.append(t.id)

    with patch("backend.worker.process_ticket", side_effect=fake_process):
        task = asyncio.create_task(analysis_loop(db_factory, concurrency=1, poll_interval=0))
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    assert processed == []
