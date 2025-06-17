import sqlite3, time, os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_transactional_outbox(tmp_path, monkeypatch):
    db = Path(__file__).parent.parent / "orders.db"
    if db.exists():
        db.unlink()

    r = client.post("/create_order", json={"user_id": 5, "amount": 123})
    assert r.status_code == 200

    time.sleep(0.1)

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM outbox")
    assert cur.fetchone()[0] >= 1
