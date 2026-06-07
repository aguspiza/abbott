"""
Minimal async in-memory store (replace with SQLAlchemy for production).
"""
from datetime import datetime, timedelta
from typing import Optional
from .models import Ticket

_store: dict[str, Ticket] = {}


class TicketDB:
    async def save(self, ticket: Ticket) -> None:
        _store[ticket.id] = ticket

    async def get(self, ticket_id: str) -> Optional[Ticket]:
        return _store.get(ticket_id)

    async def list(self, days: int = 5) -> list[Ticket]:
        tickets = list(_store.values())
        if days > 0:
            cutoff = datetime.utcnow() - timedelta(days=days)
            tickets = [t for t in tickets if t.created_at >= cutoff]
        return sorted(tickets, key=lambda t: t.created_at, reverse=True)


async def get_db() -> TicketDB:
    return TicketDB()
