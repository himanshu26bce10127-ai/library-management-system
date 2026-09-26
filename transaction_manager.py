"""
Transaction Management module (Functional Module 3).

Handles issuing books to members, processing returns, renewals, and
calculating overdue fines. This module coordinates BookManager and
MemberManager rather than touching their tables directly, keeping each
manager responsible for its own data.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from .book_manager import BookManager
from .database import Database
from .exceptions import BusinessRuleError, NotFoundError, ValidationError
from .member_manager import MemberManager
from .models import Transaction
from .utils import get_logger

logger = get_logger(__name__)

LOAN_PERIOD_DAYS = 14
FINE_PER_DAY = 5.0          # currency units per day overdue
MAX_BOOKS_PER_MEMBER = 3
MAX_OUTSTANDING_FINE = 50.0  # members above this cannot borrow more


class TransactionManager:
    def __init__(self, db: Database, book_manager: BookManager, member_manager: MemberManager):
        self.db = db
        self.books = book_manager
        self.members = member_manager

    # ---------- Issue ----------
    def issue_book(self, book_id: int, member_id: int, on_date: Optional[date] = None) -> Transaction:
        on_date = on_date or date.today()
        book = self.books.get_book(book_id)          # raises NotFoundError
        member = self.members.get_member(member_id)   # raises NotFoundError

        if member.outstanding_fine > MAX_OUTSTANDING_FINE:
            raise BusinessRuleError(
                f"Member has an outstanding fine of Rs.{member.outstanding_fine:.2f} "
                f"(limit Rs.{MAX_OUTSTANDING_FINE:.2f}); please clear it before borrowing."
            )

        active_count = self.db.query_one(
            "SELECT COUNT(*) AS c FROM transactions WHERE member_id = ? AND status = 'ISSUED'",
            (member_id,),
        )["c"]
        if active_count >= MAX_BOOKS_PER_MEMBER:
            raise BusinessRuleError(
                f"Member already has {active_count} books issued "
                f"(limit {MAX_BOOKS_PER_MEMBER}). Please return a book first."
            )

        already_has_this_book = self.db.query_one(
            """SELECT 1 FROM transactions
               WHERE member_id = ? AND book_id = ? AND status = 'ISSUED'""",
            (member_id, book_id),
        )
        if already_has_this_book:
            raise BusinessRuleError("This member already has a copy of this book issued.")

        self.books.decrement_availability(book_id)  # raises BusinessRuleError if none available

        due_date = on_date + timedelta(days=LOAN_PERIOD_DAYS)
        cur = self.db.execute(
            """INSERT INTO transactions (book_id, member_id, issue_date, due_date, status)
               VALUES (?, ?, ?, ?, 'ISSUED')""",
            (book_id, member_id, on_date.isoformat(), due_date.isoformat()),
        )
        logger.info(
            "Issued book %d ('%s') to member %d, due %s.",
            book_id, book.title, member_id, due_date.isoformat(),
        )
        return self.get_transaction(cur.lastrowid)

    # ---------- Return ----------
    def return_book(self, transaction_id: int, on_date: Optional[date] = None) -> Transaction:
        on_date = on_date or date.today()
        txn = self.get_transaction(transaction_id)
        if txn.status != "ISSUED":
            raise BusinessRuleError(f"Transaction {transaction_id} is already {txn.status.lower()}.")

        due = datetime.strptime(txn.due_date, "%Y-%m-%d").date()
        overdue_days = max(0, (on_date - due).days)
        fine = round(overdue_days * FINE_PER_DAY, 2)

        self.db.execute(
            """UPDATE transactions
               SET return_date = ?, status = 'RETURNED', fine_charged = ?
               WHERE transaction_id = ?""",
            (on_date.isoformat(), fine, transaction_id),
        )
        self.books.increment_availability(txn.book_id)
        if fine > 0:
            self.members.add_fine(txn.member_id, fine)
            logger.info(
                "Transaction %d returned %d day(s) late; fine Rs.%.2f applied.",
                transaction_id, overdue_days, fine,
            )
        else:
            logger.info("Transaction %d returned on time.", transaction_id)
        return self.get_transaction(transaction_id)

    # ---------- Renew ----------
    def renew_transaction(self, transaction_id: int, on_date: Optional[date] = None) -> Transaction:
        on_date = on_date or date.today()
        txn = self.get_transaction(transaction_id)
        if txn.status != "ISSUED":
            raise BusinessRuleError("Only currently issued books can be renewed.")
        due = datetime.strptime(txn.due_date, "%Y-%m-%d").date()
        if on_date > due:
            raise BusinessRuleError("Cannot renew an overdue book; please return and pay the fine first.")
        new_due = due + timedelta(days=LOAN_PERIOD_DAYS)
        self.db.execute(
            "UPDATE transactions SET due_date = ? WHERE transaction_id = ?",
            (new_due.isoformat(), transaction_id),
        )
        logger.info("Transaction %d renewed; new due date %s.", transaction_id, new_due.isoformat())
        return self.get_transaction(transaction_id)

    # ---------- Read ----------
    def get_transaction(self, transaction_id: int) -> Transaction:
        row = self.db.query_one(
            "SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,)
        )
        if row is None:
            raise NotFoundError(f"No transaction found with ID {transaction_id}.")
        return Transaction.from_row(row)

    def list_active_for_member(self, member_id: int) -> List[Transaction]:
        rows = self.db.query_all(
            "SELECT * FROM transactions WHERE member_id = ? AND status = 'ISSUED'",
            (member_id,),
        )
        return [Transaction.from_row(r) for r in rows]

    def list_overdue(self, as_of: Optional[date] = None) -> List[Transaction]:
        as_of = as_of or date.today()
        rows = self.db.query_all(
            "SELECT * FROM transactions WHERE status = 'ISSUED' AND due_date < ?",
            (as_of.isoformat(),),
        )
        return [Transaction.from_row(r) for r in rows]

    def list_all(self) -> List[Transaction]:
        rows = self.db.query_all("SELECT * FROM transactions ORDER BY transaction_id DESC")
        return [Transaction.from_row(r) for r in rows]
