from fastapi import FastAPI
from pydantic import BaseModel
import json
import sqlite3
from pathlib import Path
from db import db_file, conn, cursor

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
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT
        )
    """)
    conn.commit()

class OrderRequest(BaseModel):
    user_id: int
    amount: int

@app.post("/create_order")
def create_order(order: OrderRequest):
    if not db_file.exists():
        recreate_db()

    cursor.execute(
        "INSERT INTO orders (user_id, amount, status) VALUES (?, ?, ?)",
        (order.user_id, order.amount, "PENDING")
    )
    order_id = cursor.lastrowid

    payload = json.dumps({
        "order_id": order_id,
        "user_id": order.user_id,
        "amount": order.amount
    })
    cursor.execute("INSERT INTO outbox (payload) VALUES (?)", (payload,))
    conn.commit()

    return {"order_id": order_id, "status": "created"}

@app.get("/orders")
def list_orders():
    if not db_file.exists():
        recreate_db()

    cursor.execute("SELECT order_id, user_id, amount, status FROM orders")
    return [
        {"order_id": r[0], "user_id": r[1], "amount": r[2], "status": r[3]}
        for r in cursor.fetchall()
    ]

@app.get("/order_status/{order_id}")
def order_status(order_id: int):
    if not db_file.exists():
        recreate_db()

    cursor.execute("SELECT status FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    if not row:
        return {"error": "Order not found"}
    return {"status": row[0]}
