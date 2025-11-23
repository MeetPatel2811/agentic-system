# ---------------------------------------------------------
# This file implements SQLite-backed history memory:
# - Initializes the DB if needed.
# - Saves (query, response, timestamp).
# - Can fetch recent entries for the frontend.
# ---------------------------------------------------------
import os
import sqlite3
from datetime import datetime

# --- This block computes the absolute path to db/history.db ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "..", "db")
DB_PATH = os.path.abspath(os.path.join(DB_DIR, "history.db"))


def _init_db():
    """
    Create the history table if it does not exist.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            ts TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_history(query: str, response: str):
    """
    Save a new (query, response, timestamp) row into the history table.
    """
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO history (query, response, ts) VALUES (?, ?, ?)",
        (query, response, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_recent(limit: int = 10):
    """
    Return the most recent 'limit' history rows (id, query, ts).
    """
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, query, ts FROM history ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    return rows
