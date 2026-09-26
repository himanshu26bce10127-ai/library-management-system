"""
Book Management module (Functional Module 1).

Provides CRUD operations plus search for the books catalogue.
"""

from typing import List, Optional

from .database import Database
from .exceptions import BusinessRuleError, NotFoundError, ValidationError
from .models import Book
from .utils import (
    get_logger,
    require_non_empty,
    require_positive_int,
    validate_isbn,
    validate_year,
)

logger = get_logger(__name__)


class BookManager:
    def __init__(self, db: Database):
        self.db = db

    # ---------- Create ----------
    def add_book(
        self, isbn: str, title: str, author: str, category: str, year, copies
    ) -> Book:
        isbn = validate_isbn(isbn)
        title = require_non_empty(title, "Title")
        author = require_non_empty(author, "Author")
        category = require_non_empty(category, "Category")
        year = validate_year(year)
        copies = require_positive_int(copies, "Number of copies")

        existing = self.db.query_one("SELECT * FROM books WHERE isbn = ?", (isbn,))
        if existing:
            # Same ISBN added again -> top up copies instead of duplicating.
            new_total = existing["total_copies"] + copies
            new_available = existing["available_copies"] + copies
            self.db.execute(
                "UPDATE books SET total_copies = ?, available_copies = ? WHERE isbn = ?",
                (new_total, new_available, isbn),
            )
            logger.info("Topped up existing book ISBN %s by %d copies.", isbn, copies)
            return self.get_book_by_isbn(isbn)

        cur = self.db.execute(
            """INSERT INTO books (isbn, title, author, category, year, total_copies, available_copies)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (isbn, title, author, category, year, copies, copies),
        )
        logger.info("Added new book '%s' (ISBN %s).", title, isbn)
        return self.get_book(cur.lastrowid)

    # ---------- Read ----------
    def get_book(self, book_id: int) -> Book:
        row = self.db.query_one("SELECT * FROM books WHERE book_id = ?", (book_id,))
        if row is None:
            raise NotFoundError(f"No book found with ID {book_id}.")
        return Book.from_row(row)

    def get_book_by_isbn(self, isbn: str) -> Book:
        row = self.db.query_one("SELECT * FROM books WHERE isbn = ?", (isbn,))
        if row is None:
            raise NotFoundError(f"No book found with ISBN {isbn}.")
        return Book.from_row(row)

    def list_books(self) -> List[Book]:
        rows = self.db.query_all("SELECT * FROM books ORDER BY title")
        return [Book.from_row(r) for r in rows]

    def search_books(self, keyword: str) -> List[Book]:
        keyword = require_non_empty(keyword, "Search keyword")
        like = f"%{keyword}%"
        rows = self.db.query_all(
            """SELECT * FROM books
               WHERE title LIKE ? OR author LIKE ? OR category LIKE ? OR isbn LIKE ?
               ORDER BY title""",
            (like, like, like, like),
        )
        return [Book.from_row(r) for r in rows]

    # ---------- Update ----------
    def update_book(self, book_id: int, **fields) -> Book:
        book = self.get_book(book_id)  # raises NotFoundError if missing
        allowed = {"title", "author", "category", "year", "total_copies"}
        updates = {}
        for key, value in fields.items():
            if key not in allowed or value in (None, ""):
                continue
            if key == "year":
                value = validate_year(value)
            elif key == "total_copies":
                value = require_positive_int(value, "Total copies")
                borrowed = book.total_copies - book.available_copies
                if value < borrowed:
                    raise BusinessRuleError(
                        f"Cannot set total copies below {borrowed} "
                        f"(copies currently issued to members)."
                    )
                # Keep available_copies consistent with the new total.
                updates["available_copies"] = value - borrowed
            else:
                value = require_non_empty(value, key)
            updates[key] = value

        if not updates:
            return book

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = tuple(updates.values()) + (book_id,)
        self.db.execute(f"UPDATE books SET {set_clause} WHERE book_id = ?", params)
        logger.info("Updated book %d: %s", book_id, updates)
        return self.get_book(book_id)

    # ---------- Delete ----------
    def delete_book(self, book_id: int) -> None:
        book = self.get_book(book_id)
        if book.available_copies < book.total_copies:
            raise BusinessRuleError(
                "Cannot delete a book that currently has copies issued to members."
            )
        self.db.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
        logger.info("Deleted book %d ('%s').", book_id, book.title)

    # ---------- Availability helpers used by TransactionManager ----------
    def decrement_availability(self, book_id: int) -> None:
        book = self.get_book(book_id)
        if book.available_copies <= 0:
            raise BusinessRuleError(f"No available copies of '{book.title}' to issue.")
        self.db.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
            (book_id,),
        )

    def increment_availability(self, book_id: int) -> None:
        book = self.get_book(book_id)
        if book.available_copies >= book.total_copies:
            return
        self.db.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?",
            (book_id,),
        )
