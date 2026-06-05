# Abbott

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
