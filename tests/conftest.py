import pytest
import backend.db as _db_module
import backend.main as _main_module
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.db import init_db


@pytest.fixture
async def tmp_db(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(_db_module, "_DB_PATH", path)
    return path


@pytest.fixture
async def client(tmp_db, monkeypatch):
    async def _noop(*args, **kwargs):
        pass

    monkeypatch.setattr(_main_module, "analysis_loop", _noop)
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
