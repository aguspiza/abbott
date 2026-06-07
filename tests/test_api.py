import pytest
from httpx import AsyncClient


async def test_create_ticket_returns_201(client: AsyncClient):
    resp = await client.post("/api/tickets", json={"raw_log": "Process exited with code 1"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"].startswith("TKT-")
    assert data["status"] == "OPEN"
    assert data["raw_log"] == "Process exited with code 1"


async def test_create_ticket_extracts_job_name_from_url(client: AsyncClient):
    resp = await client.post("/api/tickets", json={
        "raw_log": "fail",
        "build_url": "https://jenkins.example.com/job/my-pipeline/job/feature-branch/42/",
    })
    assert resp.status_code == 201
    assert resp.json()["job_name"] == "my-pipeline/feature-branch"


async def test_create_ticket_explicit_job_name_wins(client: AsyncClient):
    resp = await client.post("/api/tickets", json={
        "raw_log": "fail",
        "job_name": "override-name",
        "build_url": "https://jenkins.example.com/job/other/1/",
    })
    assert resp.status_code == 201
    assert resp.json()["job_name"] == "override-name"


async def test_get_ticket_returns_ticket(client: AsyncClient):
    create = await client.post("/api/tickets", json={"raw_log": "err"})
    ticket_id = create.json()["id"]
    resp = await client.get(f"/api/tickets/{ticket_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == ticket_id


async def test_get_ticket_not_found(client: AsyncClient):
    resp = await client.get("/api/tickets/TKT-NOTREAL")
    assert resp.status_code == 404


async def test_list_tickets_returns_all(client: AsyncClient):
    await client.post("/api/tickets", json={"raw_log": "a"})
    await client.post("/api/tickets", json={"raw_log": "b"})
    resp = await client.get("/api/tickets?days=0")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


async def test_add_note_appends_and_reopens(client: AsyncClient):
    create = await client.post("/api/tickets", json={"raw_log": "err"})
    ticket_id = create.json()["id"]
    resp = await client.post(
        f"/api/tickets/{ticket_id}/notes",
        json={"note": "Check disk space"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Check disk space" in data["notes"]
    assert data["status"] == "OPEN"


async def test_add_note_not_found(client: AsyncClient):
    resp = await client.post("/api/tickets/TKT-NOTREAL/notes", json={"note": "x"})
    assert resp.status_code == 404


async def test_add_multiple_notes_accumulate(client: AsyncClient):
    create = await client.post("/api/tickets", json={"raw_log": "err"})
    ticket_id = create.json()["id"]
    await client.post(f"/api/tickets/{ticket_id}/notes", json={"note": "first"})
    resp = await client.post(f"/api/tickets/{ticket_id}/notes", json={"note": "second"})
    notes = resp.json()["notes"]
    assert "first" in notes
    assert "second" in notes
