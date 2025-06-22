from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import sqlite3
import json
from pathlib import Path
from db import db_file, conn, cursor, processed_messages, balances_db

app = FastAPI()

def recreate_db():
    global conn, cursor
    try:
        conn.close()
    except:
        pass
    conn = sqlite3.connect(db_file, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_messages (
        message_id TEXT PRIMARY KEY
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS balances (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER NOT NULL
    )
    """)
    conn.commit()

class Payment(BaseModel):
    user_id: int
    amount: int

@app.post("/create_account")
def create_account(payment: Payment):
    if not db_file.exists():
        recreate_db()
    if payment.user_id in balances_db:
        raise HTTPException(status_code=400, detail="Account already exists")
    balances_db[payment.user_id] = 0
    return {"status": "created"}

@app.post("/topup")
def topup(payment: Payment):
    if payment.user_id not in balances_db:
        raise HTTPException(status_code=404, detail="No account")
    balances_db[payment.user_id] += payment.amount
    return {"status": "topped_up", "new_balance": balances_db[payment.user_id]}

@app.get("/balance/{user_id}")
def get_balance(user_id: int):
    if not db_file.exists():
        recreate_db()
    if user_id not in balances_db:
        raise HTTPException(status_code=404, detail="User not found")
    return {"balance": balances_db[user_id]}

@app.post("/credit")
async def credit(request: Request):
    raw = await request.body()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty body")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not db_file.exists():
        recreate_db()
    data = await request.json()
    message_id = data.get("message_id")
    user_id = data.get("user_id")
    amount = data.get("amount")
    if not message_id or not isinstance(user_id, int) or not isinstance(amount, int):
        raise HTTPException(status_code=400, detail="Invalid data")
    if message_id in processed_messages:
        return {"status": "already_processed"}
    balances_db.setdefault(user_id, 0)
    balances_db[user_id] += amount
    cursor.execute("""
    INSERT INTO balances (user_id, balance)
    VALUES (?, ?)
    ON CONFLICT(user_id) DO UPDATE SET balance = balance + excluded.balance
    """, (user_id, amount))
    conn.commit()
    processed_messages.add(message_id)
    return {"status": "credited"}

@app.post("/withdraw")
def withdraw(payment: Payment):
    if not db_file.exists():
        recreate_db()
    if payment.user_id not in balances_db or balances_db[payment.user_id] < payment.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    balances_db[payment.user_id] -= payment.amount
    return {"status": "paid"}

import queue_consumer
