"""
Database access layer.

Uses Python's built-in sqlite3 module so the project runs with zero
external dependencies. All schema definitions (the ER design) live here
in one place so the data model is easy to audit.
"""

import os
import sqlite3

from .utils import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "library.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    book_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn         TEXT NOT NULL UNIQUE,
    title        TEXT NOT NULL,
    author       TEXT NOT NULL,
    category     TEXT NOT NULL,
    year         INTEGER NOT NULL,
    total_copies INTEGER NOT NULL,
    available_copies INTEGER NOT NULL,
    created_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS members (
    member_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    email        TEXT NOT NULL UNIQUE,
    phone        TEXT NOT NULL,
    membership_type TEXT NOT NULL DEFAULT 'STANDARD',
    outstanding_fine REAL NOT NULL DEFAULT 0,
    created_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id      INTEGER NOT NULL,
    member_id    INTEGER NOT NULL,
    issue_date   TEXT NOT NULL,
    due_date     TEXT NOT NULL,
    return_date  TEXT,
    fine_charged REAL NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'ISSUED',
    FOREIGN KEY (book_id) REFERENCES books (book_id),
    FOREIGN KEY (member_id) REFERENCES members (member_id)
);

CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions (status);
CREATE INDEX IF NOT EXISTS idx_books_title ON books (title);
CREATE INDEX IF NOT EXISTS idx_members_email ON members (email);
"""


class Database:
    """Thin wrapper around sqlite3 that owns the connection lifecycle."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._initialize_schema()
        logger.info("Connected to database at %s", self.db_path)

    def _initialize_schema(self):
        with self.conn:
            self.conn.executescript(SCHEMA)

    def execute(self, query: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()
        return cur

    def query_one(self, query: str, params: tuple = ()):
        cur = self.conn.execute(query, params)
        return cur.fetchone()

    def query_all(self, query: str, params: tuple = ()):
        cur = self.conn.execute(query, params)
        return cur.fetchall()

    def close(self):
        self.conn.close()
