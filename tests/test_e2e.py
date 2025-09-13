from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# set env for alembic before importing app
tmpdir = tempfile.mkdtemp()
os.environ["SYNC_DATABASE_URL"] = f"sqlite:///{tmpdir}/app.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmpdir}/app.db"
os.environ["INITIAL_ADMIN_EMAIL"] = "test@example.com"
os.environ["INITIAL_ADMIN_PASSWORD"] = "testpass"

from app.main import app  # noqa: E402
from scripts.seed import main as seed_main  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def env_setup():
    os.makedirs("data", exist_ok=True)
    os.system("alembic upgrade head")
    seed_main()
    yield


def test_e2e_flow():
    client = TestClient(app)
    r = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass"})
    assert r.status_code == 200
    token = r.json()["token"]
    r = client.post("/tasks/nl", json={"text": "email sara tomorrow at 9 #work !high"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    r = client.get("/tasks/?view=today", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
