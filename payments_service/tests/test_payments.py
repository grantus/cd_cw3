import pytest
from fastapi.testclient import TestClient
from main import app, balances_db, processed_messages

client = TestClient(app)

def test_create_and_topup_and_balance():
    client.post("/create_account", json={"user_id": 1, "amount": 0})
    r = client.post("/topup", json={"user_id": 1, "amount": 200})
    assert r.status_code == 200 and r.json()["new_balance"] == 200
    r2 = client.get("/balance/1")
    assert r2.json()["balance"] == 200

def test_withdraw_success():
    client.post("/create_account", json={"user_id": 2, "amount": 0})
    balances_db[2] = 300
    r = client.post("/withdraw", json={"user_id": 2, "amount": 100})
    assert r.status_code == 200 and r.json()["status"] == "paid"

def test_withdraw_insufficient():
    client.post("/create_account", json={"user_id": 3, "amount": 0})
    r = client.post("/withdraw", json={"user_id": 3, "amount": 50})
    assert r.status_code == 400
    assert r.json() == {"detail": "Insufficient funds"}

def test_credit_and_dedup():
    client.post("/create_account", json={"user_id": 4, "amount": 0})
    msg = {"message_id": "m1", "user_id": 4, "amount": 50}
    if "m1" in processed_messages:
        processed_messages.remove("m1")
    r1 = client.post("/credit", json=msg)
    assert r1.status_code == 200 and r1.json()["status"] == "credited"
    r2 = client.post("/credit", json=msg)
    assert r2.status_code == 200 and r2.json()["status"] == "already_processed"
    assert balances_db[4] == 50
