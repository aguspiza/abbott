#!/usr/bin/env bash
# ============================================================
# bootstrap.sh — Abbott project bootstrapper
# Usage: GITHUB_TOKEN=ghp_xxx bash bootstrap.sh
# ============================================================
set -euo pipefail

GITHUB_TOKEN="${GITHUB_TOKEN:?ERROR: set GITHUB_TOKEN before running this script}"
REPO="aguspiza/abbott"
BRANCH="main"
API="https://api.github.com/repos/${REPO}/contents"

# Colour helpers
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
info() { echo -e "${YELLOW}…${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*"; exit 1; }

push_file() {
  local path="$1"
  local content_b64
  content_b64=$(printf '%s' "$2" | base64 | tr -d '\n')

  # Check if file already exists (get its SHA for update)
  local sha=""
  local existing
  existing=$(curl -sf -H "Authorization: token ${GITHUB_TOKEN}" \
    "${API}/${path}?ref=${BRANCH}" 2>/dev/null || true)
  if [[ -n "$existing" ]]; then
    sha=$(echo "$existing" | python3 -c "import sys,json; print(json.load(sys.stdin).get('sha',''))" 2>/dev/null || true)
  fi

  local payload
  if [[ -n "$sha" ]]; then
    payload=$(python3 -c "import json; print(json.dumps({'message':'chore: update ${path}','content':'${content_b64}','branch':'${BRANCH}','sha':'${sha}'}))")
  else
    payload=$(python3 -c "import json; print(json.dumps({'message':'feat: add ${path}','content':'${content_b64}','branch':'${BRANCH}'}))")
  fi

  local http_code
  http_code=$(curl -sf -o /dev/null -w "%{http_code}" \
    -X PUT "${API}/${path}" \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$payload" 2>/dev/null)

  if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
    ok "${path}"
  else
    err "Failed to push ${path} (HTTP ${http_code})"
  fi
}

echo ""
echo "🚀 Abbott — bootstrapping https://github.com/${REPO}"
echo ""

# ── README.md ────────────────────────────────────────────────
info "README.md"
push_file "README.md" '# Abbott

> AI-powered Jenkins pipeline failure investigator.

Paste a Jenkins error → get a ticket → AI investigates → Teams notification + optional Jira bug + KB entry.

## Stack
- **Backend**: FastAPI + SQLAlchemy (SQLite/Postgres)
- **AI**: Claude (Anthropic API)
- **Outputs**: Microsoft Teams webhook, Jira REST API v3, Git wiki (GitHub/GitLab)
- **Frontend**: React + TypeScript (Vite)

## Quick start

```bash
cp .env.example .env
# fill in your keys
docker-compose up
```

## Flow

```
Jenkins log paste
      │
      ▼
  POST /tickets
      │
      ▼
  parse_log()          ← regex enrichment (stage, exit code, exception…)
      │
      ▼
  investigate()        ← Claude API, structured markdown report
      │
      ▼
  severity branch
  ├── flaky/warning  → Teams notification
  └── bug            → Teams + Jira ticket
      │
      ▼
  write KB entry      ← Git wiki markdown
```

## Project structure

```
backend/
  main.py             FastAPI app + routes
  models.py           Pydantic schemas (Ticket, Severity…)
  parser.py           Jenkins log enricher
  investigator.py     Claude API integration
  worker.py           Async investigation pipeline
  integrations/
    teams.py          Teams Adaptive Card builder (mocked)
    jira.py           Jira issue builder (mocked)
    git_wiki.py       KB markdown writer (mocked)
frontend/
  src/
    pages/
      SubmitTicket.tsx
      TicketDetail.tsx
    components/
      PayloadViewer.tsx
prompts/
  investigate.md      System prompt for Claude
```
'

# ── .env.example ─────────────────────────────────────────────
info ".env.example"
push_file ".env.example" 'ANTHROPIC_API_KEY=sk-ant-...
TEAMS_WEBHOOK=https://outlook.office.com/webhook/...
JIRA_URL=https://yourorg.atlassian.net
JIRA_TOKEN=
GITHUB_TOKEN=
WIKI_REPO=yourorg/jenkins-kb
DATABASE_URL=sqlite:///./tickets.db
'

# ── docker-compose.yml ───────────────────────────────────────
info "docker-compose.yml"
push_file "docker-compose.yml" 'version: "3.9"
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    volumes:
      - ./prompts:/app/prompts
    command: uvicorn main:app --host 0.0.0.0 --reload

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on: [api]
'

# ── backend/models.py ────────────────────────────────────────
info "backend/models.py"
push_file "backend/models.py" 'from enum import Enum
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


class Ticket(BaseModel):
    id: str
    job_name: Optional[str]
    build_url: Optional[str]
    raw_log: str
    parsed: Optional[dict] = None        # enriched fields from parser
    status: TicketStatus
    severity: Optional[Severity] = None
    investigation: Optional[str] = None  # markdown report from Claude
    teams_payload: Optional[dict] = None # mocked output
    jira_payload: Optional[dict] = None  # mocked output, if bug
    wiki_payload: Optional[dict] = None  # mocked output
    created_at: datetime
    updated_at: datetime
'

# ── backend/parser.py ────────────────────────────────────────
info "backend/parser.py"
push_file "backend/parser.py" 'import re
from typing import Optional

# Patterns to extract signal from Jenkins logs
PATTERNS = {
    "exit_code":  r"Process exited with code (\d+)",
    "stage":      r"\[Pipeline\] stage\s*\n\[Pipeline\] \{ \((.+?)\)",
    "exception":  r"([\w\.]+Exception[^\n]*)",
    "error_line": r"ERROR: (.+)",
    "oom":        r"(OutOfMemoryError|Cannot allocate memory|OOMKilled)",
    "timeout":    r"(Timeout|timed out|deadline exceeded)",
    "test_fail":  r"Tests run: \d+, Failures: (\d+), Errors: (\d+)",
    "docker_err": r"(docker: Error|manifest unknown|denied: access forbidden)",
}


def parse_log(raw_log: str) -> dict:
    """Extract structured fields from a raw Jenkins log."""
    result: dict = {}
    for key, pattern in PATTERNS.items():
        match = re.search(pattern, raw_log, re.IGNORECASE | re.MULTILINE)
        if match:
            result[key] = match.group(1) if match.lastindex else match.group(0)

    # Heuristic severity pre-classification (AI will refine)
    if result.get("oom") or result.get("exception"):
        result["hint_severity"] = "bug"
    elif result.get("timeout"):
        result["hint_severity"] = "flaky"
    elif result.get("test_fail"):
        result["hint_severity"] = "bug"
    else:
        result["hint_severity"] = "unknown"

    # Truncate log to last N lines for prompt (avoid token explosion)
    lines = raw_log.strip().splitlines()
    result["tail"] = "\n".join(lines[-80:])
    result["total_lines"] = len(lines)

    return result
'

# ── backend/investigator.py ──────────────────────────────────
info "backend/investigator.py"
push_file "backend/investigator.py" 'import anthropic
from pathlib import Path
from .models import Ticket, Severity

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

SYSTEM_PROMPT = Path(__file__).parent.parent / "prompts" / "investigate.md"


def investigate(ticket: Ticket) -> dict:
    """
    Call Claude to investigate a parsed Jenkins failure.
    Returns structured investigation result.
    """
    system = SYSTEM_PROMPT.read_text()
    parsed = ticket.parsed or {}

    user_msg = f"""## Jenkins Failure Report

**Job**: {ticket.job_name or "unknown"}
**Build URL**: {ticket.build_url or "unknown"}
**Parsed fields**: {parsed}

## Log tail (last 80 lines)
```
{parsed.get("tail", ticket.raw_log[-3000:])}
```
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text

    return {
        "report":     text,
        "severity":   _extract_severity(text),
        "summary":    _extract_section(text, "## Summary"),
        "root_cause": _extract_section(text, "## Root Cause"),
        "fix":        _extract_section(text, "## Fix"),
    }


def _extract_severity(text: str) -> Severity:
    t = text.lower()
    if "severity: bug" in t or "regression" in t:
        return Severity.BUG
    if "severity: flaky" in t or "transient" in t:
        return Severity.FLAKY
    if "severity: warning" in t:
        return Severity.WARNING
    return Severity.UNKNOWN


def _extract_section(text: str, header: str) -> str:
    lines = text.splitlines()
    capture, out = False, []
    for line in lines:
        if line.strip().startswith(header):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            out.append(line)
    return "\n".join(out).strip()
'

# ── backend/worker.py ────────────────────────────────────────
info "backend/worker.py"
push_file "backend/worker.py" 'from .models import Ticket, TicketStatus
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
'

# ── backend/main.py ──────────────────────────────────────────
info "backend/main.py"
push_file "backend/main.py" 'import uuid
from datetime import datetime

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import get_db
from .models import Ticket, TicketCreate, TicketStatus
from .worker import process_ticket

app = FastAPI(title="Abbott — Jenkins Investigator")
app.add_middleware(CORSMiddleware, allow_origins=["*"])


@app.post("/tickets", response_model=Ticket, status_code=201)
async def create_ticket(
    body: TicketCreate,
    bg: BackgroundTasks,
    db=Depends(get_db),
):
    now = datetime.utcnow()
    ticket = Ticket(
        id=f"TKT-{uuid.uuid4().hex[:8].upper()}",
        status=TicketStatus.OPEN,
        created_at=now,
        updated_at=now,
        **body.dict(),
    )
    await db.save(ticket)
    bg.add_task(process_ticket, ticket, db)  # fire and forget
    return ticket


@app.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str, db=Depends(get_db)):
    return await db.get(ticket_id)


@app.get("/tickets", response_model=list[Ticket])
async def list_tickets(db=Depends(get_db)):
    return await db.list()
'

# ── backend/config.py ────────────────────────────────────────
info "backend/config.py"
push_file "backend/config.py" 'from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    teams_webhook: str     = ""
    jira_url: str          = ""
    jira_token: str        = ""
    github_token: str      = ""
    wiki_repo: str         = ""
    database_url: str      = "sqlite:///./tickets.db"

    class Config:
        env_file = ".env"


settings = Settings()
'

# ── backend/db.py ────────────────────────────────────────────
info "backend/db.py"
push_file "backend/db.py" '"""
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
'

# ── backend/__init__.py ──────────────────────────────────────
info "backend/__init__.py"
push_file "backend/__init__.py" ''

# ── backend/integrations/__init__.py ────────────────────────
info "backend/integrations/__init__.py"
push_file "backend/integrations/__init__.py" ''

# ── backend/integrations/teams.py ───────────────────────────
info "backend/integrations/teams.py"
push_file "backend/integrations/teams.py" '# MOCKED — replace body of send_teams() with a real httpx.post call


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
'

# ── backend/integrations/jira.py ────────────────────────────
info "backend/integrations/jira.py"
push_file "backend/integrations/jira.py" '# MOCKED — replace body of create_jira_issue() with a real httpx.post call


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
'

# ── backend/integrations/git_wiki.py ────────────────────────
info "backend/integrations/git_wiki.py"
push_file "backend/integrations/git_wiki.py" '# MOCKED — replace body of write_wiki_entry() with a real GitHub/GitLab API call
import base64


def build_wiki_entry(ticket, investigation: dict) -> dict:
    """Build a KB markdown entry for the Git wiki."""
    tags = investigation.get("report", "").split("## KB Tags")[-1].strip()
    slug = ticket.id.lower().replace("-", "_")

    content = f"""# [{ticket.id}] {ticket.job_name} failure

**Date**: {ticket.created_at}
**Severity**: {ticket.severity}
**Tags**: {tags}

## Summary
{investigation.get("summary", "")}

## Root Cause
{investigation.get("root_cause", "")}

## Fix
{investigation.get("fix", "")}

## References
- Jenkins build: {ticket.build_url}
- Ticket: {ticket.id}
"""
    return {
        "path":    f"kb/investigations/{slug}.md",
        "message": f"docs(kb): add investigation {ticket.id}",
        "content": content,
    }


async def write_wiki_entry(payload: dict, repo: str, token: str) -> None:
    # MOCK: log payload instead of writing
    print("[MOCK WIKI]", payload)
    # Real implementation (GitHub Contents API):
    # import httpx, base64
    # encoded = base64.b64encode(payload["content"].encode()).decode()
    # async with httpx.AsyncClient() as client:
    #     await client.put(
    #         f"https://api.github.com/repos/{repo}/contents/{payload['\''path'\'']}",
    #         headers={"Authorization": f"Bearer {token}"},
    #         json={"message": payload["message"], "content": encoded},
    #     )
'

# ── prompts/investigate.md ───────────────────────────────────
info "prompts/investigate.md"
push_file "prompts/investigate.md" 'You are a senior DevOps engineer specialising in CI/CD pipeline failure analysis.

Given a Jenkins build failure, produce a structured investigation report with these exact sections:

## Summary
One sentence: what failed and why.

## Severity
One of: `bug` | `flaky` | `warning`
- **bug**: reproducible regression, needs a Jira ticket
- **flaky**: transient failure (network, race condition, resource spike) — retry may fix it
- **warning**: non-blocking, informational only

## Root Cause
Technical explanation. Reference the exact log lines or error codes.
Mention the relevant Jenkins stage, Docker layer, test class, or dependency if identifiable.

## Fix
Concrete recommended action:
- **bug**: what to change in code/config and in which repo/file
- **flaky**: retry strategy, resource limits, or environment fix
- **warning**: monitoring recommendation

## KB Tags
Comma-separated lowercase keywords for knowledge base indexing.
Examples: `docker, image-pull, registry-auth` or `maven, oom, heap-size`

---
Rules:
- Be concise. No waffle.
- Avoid speculation beyond what the log shows.
- If the log appears truncated, state it explicitly.
- Always output all five sections, even if some are brief.
'

# ── backend/requirements.txt ─────────────────────────────────
info "backend/requirements.txt"
push_file "backend/requirements.txt" 'anthropic>=0.28.0
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
httpx>=0.27.0
'

# ── backend/Dockerfile ───────────────────────────────────────
info "backend/Dockerfile"
push_file "backend/Dockerfile" 'FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'

echo ""
echo "✅  All files pushed to https://github.com/${REPO}"
echo ""
echo "Next steps:"
echo "  git clone https://github.com/${REPO}.git"
echo "  cd abbott && cp .env.example .env"
echo "  # fill in ANTHROPIC_API_KEY and other vars"
echo "  docker-compose up"
echo ""

