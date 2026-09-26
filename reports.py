"""
Reporting & Analytics module (Functional Module 4).

Aggregates data across books, members and transactions to produce
management-style reports. Kept read-only and separate from the CRUD
managers so reporting logic can evolve independently.
"""

from datetime import date
from typing import List, Tuple

from .database import Database
from .transaction_manager import TransactionManager
from .utils import get_logger

logger = get_logger(__name__)


class ReportManager:
    def __init__(self, db: Database, transaction_manager: TransactionManager):
        self.db = db
        self.transactions = transaction_manager

    def most_borrowed_books(self, limit: int = 5) -> List[Tuple[str, int]]:
        rows = self.db.query_all(
            """SELECT b.title AS title, COUNT(*) AS borrow_count
               FROM transactions t JOIN books b ON t.book_id = b.book_id
               GROUP BY t.book_id
               ORDER BY borrow_count DESC
               LIMIT ?""",
            (limit,),
        )
        return [(r["title"], r["borrow_count"]) for r in rows]

    def overdue_report(self) -> List[dict]:
        overdue = self.transactions.list_overdue()
        result = []
        today = date.today()
        for txn in overdue:
            book = self.db.query_one(
                "SELECT title FROM books WHERE book_id = ?", (txn.book_id,)
            )
            member = self.db.query_one(
                "SELECT name, email FROM members WHERE member_id = ?", (txn.member_id,)
            )
            due = date.fromisoformat(txn.due_date)
            days_overdue = (today - due).days
            result.append(
                {
                    "transaction_id": txn.transaction_id,
                    "book_title": book["title"] if book else "Unknown",
                    "member_name": member["name"] if member else "Unknown",
                    "member_email": member["email"] if member else "Unknown",
                    "due_date": txn.due_date,
                    "days_overdue": days_overdue,
                    "estimated_fine": round(days_overdue * 5.0, 2),
                }
            )
        return result

    def library_summary(self) -> dict:
        total_books = self.db.query_one("SELECT COUNT(*) AS c FROM books")["c"]
        total_copies = self.db.query_one(
            "SELECT COALESCE(SUM(total_copies), 0) AS c FROM books"
        )["c"]
        available_copies = self.db.query_one(
            "SELECT COALESCE(SUM(available_copies), 0) AS c FROM books"
        )["c"]
        total_members = self.db.query_one("SELECT COUNT(*) AS c FROM members")["c"]
        active_loans = self.db.query_one(
            "SELECT COUNT(*) AS c FROM transactions WHERE status = 'ISSUED'"
        )["c"]
        total_fines_outstanding = self.db.query_one(
            "SELECT COALESCE(SUM(outstanding_fine), 0) AS c FROM members"
        )["c"]
        total_fines_collected = self.db.query_one(
            "SELECT COALESCE(SUM(fine_charged), 0) AS c FROM transactions WHERE status = 'RETURNED'"
        )["c"]
        return {
            "total_books": total_books,
            "total_copies": total_copies,
            "available_copies": available_copies,
            "issued_copies": total_copies - available_copies,
            "total_members": total_members,
            "active_loans": active_loans,
            "total_fines_outstanding": round(total_fines_outstanding, 2),
            "total_fines_collected_historically": round(total_fines_collected, 2),
        }

    def category_distribution(self) -> List[Tuple[str, int]]:
        rows = self.db.query_all(
            "SELECT category, COUNT(*) AS c FROM books GROUP BY category ORDER BY c DESC"
        )
        return [(r["category"], r["c"]) for r in rows]
