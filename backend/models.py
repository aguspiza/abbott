from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TicketStatus(str, Enum):
    OPEN          = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED      = "RESOLVED"
    FAILED        = "FAILED"


class Severity(str, Enum):
    FLAKY   = "flaky"    # transient / retry candidate
    WARNING = "warning"  # non-blocking, Teams only
    BUG     = "bug"      # regression, Teams + Jira
    UNKNOWN = "unknown"


class TicketCreate(BaseModel):
    raw_log: str
    job_name: Optional[str] = None
    build_url: Optional[str] = None


class NoteCreate(BaseModel):
    note: str


class Ticket(BaseModel):
    id: str
    job_name: Optional[str]
    build_url: Optional[str]
    raw_log: str
    parsed: Optional[dict] = None        # enriched fields from parser
    status: TicketStatus
    severity: Optional[Severity] = None
    investigation: Optional[str] = None  # markdown report from Claude
    notes: list[str] = []                # user-supplied additional context
    teams_payload: Optional[dict] = None # mocked output
    jira_payload: Optional[dict] = None  # mocked output, if bug
    wiki_payload: Optional[dict] = None  # mocked output
    created_at: datetime
    updated_at: datetime
