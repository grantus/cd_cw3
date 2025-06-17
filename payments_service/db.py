import sqlite3
from pathlib import Path

db_file = Path(__file__).parent / "payments.db"

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

processed_messages = set()
balances_db = {}
