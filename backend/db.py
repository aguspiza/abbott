"""
Minimal async in-memory store (replace with SQLAlchemy for production).
"""
from typing import Optional
from .models import Ticket

_store: dict[str, Ticket] = {}


class TicketDB:
    async def save(self, ticket: Ticket) -> None:
        _store[ticket.id] = ticket

    async def get(self, ticket_id: str) -> Optional[Ticket]:
        return _store.get(ticket_id)

    async def list(self) -> list[Ticket]:
        return list(_store.values())


async def get_db() -> TicketDB:
    return TicketDB()
