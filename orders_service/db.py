from pathlib import Path
import sqlite3

db_file = Path(__file__).parent / "orders.db"

conn = sqlite3.connect(db_file, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id  INTEGER NOT NULL,
        amount   INTEGER NOT NULL,
        status   TEXT    NOT NULL
    );
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS outbox (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        payload TEXT    NOT NULL,
        sent    INTEGER NOT NULL DEFAULT 0
    );
"""
)

conn.commit()

try:
    cursor.execute("ALTER TABLE outbox ADD COLUMN sent INTEGER DEFAULT 0;")
    conn.commit()
except sqlite3.OperationalError:
    pass
