"""
Librarian authentication.

A minimal but real authentication layer: passwords are never stored or
compared in plaintext, they are salted and hashed with SHA-256. This
satisfies the 'Security' non-functional requirement without pulling in
an external dependency.
"""

import hashlib
import os
import secrets

from .database import Database
from .exceptions import AuthenticationError, ValidationError
from .utils import get_logger, require_non_empty

logger = get_logger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS librarians (
    username TEXT PRIMARY KEY,
    salt     TEXT NOT NULL,
    password_hash TEXT NOT NULL
);
"""


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


class AuthManager:
    def __init__(self, db: Database):
        self.db = db
        with self.db.conn:
            self.db.conn.executescript(SCHEMA)
        self._ensure_default_admin()

    def _ensure_default_admin(self):
        """Create a default admin/admin123 account on first run only."""
        row = self.db.query_one("SELECT * FROM librarians WHERE username = ?", ("admin",))
        if row is None:
            self.register("admin", "admin123")
            logger.info("Default librarian account 'admin' created.")

    def register(self, username: str, password: str) -> None:
        username = require_non_empty(username, "Username")
        password = require_non_empty(password, "Password")
        if len(password) < 6:
            raise ValidationError("Password must be at least 6 characters long.")
        existing = self.db.query_one(
            "SELECT 1 FROM librarians WHERE username = ?", (username,)
        )
        if existing:
            raise ValidationError(f"Username '{username}' already exists.")
        salt = secrets.token_hex(16)
        password_hash = _hash_password(password, salt)
        self.db.execute(
            "INSERT INTO librarians (username, salt, password_hash) VALUES (?, ?, ?)",
            (username, salt, password_hash),
        )
        logger.info("Registered new librarian account: %s", username)

    def login(self, username: str, password: str) -> bool:
        row = self.db.query_one(
            "SELECT * FROM librarians WHERE username = ?", (username,)
        )
        if row is None:
            logger.warning("Failed login attempt for unknown user: %s", username)
            raise AuthenticationError("Invalid username or password.")
        expected_hash = _hash_password(password, row["salt"])
        if not secrets.compare_digest(expected_hash, row["password_hash"]):
            logger.warning("Failed login attempt for user: %s", username)
            raise AuthenticationError("Invalid username or password.")
        logger.info("Successful login: %s", username)
        return True
