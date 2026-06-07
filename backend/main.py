import re
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .db import get_db, init_db
from .models import Ticket, TicketCreate, TicketStatus, NoteCreate
from .worker import process_ticket

app = FastAPI(title="Abbott — Jenkins Investigator")
app.add_middleware(CORSMiddleware, allow_origins=["*"])


@app.on_event("startup")
async def startup():
    await init_db()

router = APIRouter(prefix="/api")


def _job_name_from_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = re.findall(r'/job/([^/]+)', url)
    return '/'.join(parts) if parts else None


@router.post("/tickets", response_model=Ticket, status_code=201)
async def create_ticket(
    body: TicketCreate,
    bg: BackgroundTasks,
    db=Depends(get_db),
):
    now = datetime.utcnow()
    data = body.dict()
    if not data.get('job_name'):
        data['job_name'] = _job_name_from_url(data.get('build_url'))
    ticket = Ticket(
        id=f"TKT-{uuid.uuid4().hex[:8].upper()}",
        status=TicketStatus.OPEN,
        created_at=now,
        updated_at=now,
        **data,
    )
    await db.save(ticket)
    bg.add_task(process_ticket, ticket, db)
    return ticket


@app.post("/tickets/{ticket_id}/notes", response_model=Ticket)
async def add_note(
    ticket_id: str,
    body: NoteCreate,
    bg: BackgroundTasks,
    db=Depends(get_db),
):
    ticket = await db.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.notes.append(body.note)
    ticket.status = TicketStatus.OPEN
    ticket.updated_at = datetime.utcnow()
    await db.save(ticket)
    bg.add_task(process_ticket, ticket, db)
    return ticket


@app.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str, db=Depends(get_db)):
    ticket = await db.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/tickets", response_model=list[Ticket])
async def list_tickets(days: int = 5, db=Depends(get_db)):
    return await db.list(days=days)


app.include_router(router)
