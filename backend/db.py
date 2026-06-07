import aiosqlite
from datetime import datetime, timedelta
from typing import Optional
from .models import Ticket
from .config import settings

_DB_PATH = settings.database_url.replace("sqlite:///", "")


async def init_db() -> None:
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS tickets "
            "(id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        await db.commit()


class TicketDB:
    async def save(self, ticket: Ticket) -> None:
        async with aiosqlite.connect(_DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO tickets (id, data) VALUES (?, ?)",
                (ticket.id, ticket.model_dump_json()),
            )
            await db.commit()

    async def get(self, ticket_id: str) -> Optional[Ticket]:
        async with aiosqlite.connect(_DB_PATH) as db:
            async with db.execute(
                "SELECT data FROM tickets WHERE id = ?", (ticket_id,)
            ) as cur:
                row = await cur.fetchone()
        return Ticket.model_validate_json(row[0]) if row else None

    async def list(self, days: int = 5) -> list[Ticket]:
        async with aiosqlite.connect(_DB_PATH) as db:
            async with db.execute(
                "SELECT data FROM tickets "
                "ORDER BY json_extract(data, '$.created_at') DESC"
            ) as cur:
                rows = await cur.fetchall()
        tickets = [Ticket.model_validate_json(row[0]) for row in rows]
        if days > 0:
            cutoff = datetime.utcnow() - timedelta(days=days)
            tickets = [t for t in tickets if t.created_at >= cutoff]
        return tickets


async def get_db() -> TicketDB:
    return TicketDB()
