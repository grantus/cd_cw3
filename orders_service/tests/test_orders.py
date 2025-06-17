import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_order():
    r = client.post("/create_order", json={"user_id": 1, "amount": 100})
    assert r.status_code == 200
    assert r.json()["status"] == "created"

def test_list_and_status():
    r1 = client.post("/create_order", json={"user_id": 2, "amount": 50})
    oid = r1.json()["order_id"]
    r2 = client.get("/orders")
    assert any(o["order_id"] == oid for o in r2.json())
    r3 = client.get(f"/order_status/{oid}")
    assert "status" in r3.json()
