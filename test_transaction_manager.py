import os
import sys
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.book_manager import BookManager
from src.database import Database
from src.exceptions import BusinessRuleError, NotFoundError
from src.member_manager import MemberManager
from src.transaction_manager import (
    FINE_PER_DAY,
    LOAN_PERIOD_DAYS,
    MAX_BOOKS_PER_MEMBER,
    TransactionManager,
)


class TestTransactionManager(unittest.TestCase):
    def setUp(self):
        self.db = Database(db_path=":memory:")
        self.books = BookManager(self.db)
        self.members = MemberManager(self.db)
        self.txns = TransactionManager(self.db, self.books, self.members)

        self.book = self.books.add_book(
            "9780134685991", "Effective Java", "Joshua Bloch", "Programming", 2018, 2
        )
        self.member = self.members.add_member("Asha Rao", "asha@example.com", "9876543210")

    def tearDown(self):
        self.db.close()

    def test_issue_book_success(self):
        txn = self.txns.issue_book(self.book.book_id, self.member.member_id)
        self.assertEqual(txn.status, "ISSUED")
        book = self.books.get_book(self.book.book_id)
        self.assertEqual(book.available_copies, 1)

        expected_due = date.today() + timedelta(days=LOAN_PERIOD_DAYS)
        self.assertEqual(txn.due_date, expected_due.isoformat())

    def test_issue_book_no_copies_left(self):
        self.txns.issue_book(self.book.book_id, self.member.member_id)
        other_member = self.members.add_member("Ravi Kumar", "ravi@example.com", "9123456780")
        self.txns.issue_book(self.book.book_id, other_member.member_id)  # 2nd copy taken
        third_member = self.members.add_member("Meera Iyer", "meera@example.com", "9012345678")
        with self.assertRaises(BusinessRuleError):
            self.txns.issue_book(self.book.book_id, third_member.member_id)

    def test_member_cannot_exceed_max_books(self):
        titles = []
        for i in range(MAX_BOOKS_PER_MEMBER + 1):
            b = self.books.add_book(
                f"978000000000{i}", f"Book {i}", "Author", "Category", 2020, 1
            )
            titles.append(b)
        for i in range(MAX_BOOKS_PER_MEMBER):
            self.txns.issue_book(titles[i].book_id, self.member.member_id)
        with self.assertRaises(BusinessRuleError):
            self.txns.issue_book(titles[MAX_BOOKS_PER_MEMBER].book_id, self.member.member_id)

    def test_return_book_on_time_no_fine(self):
        txn = self.txns.issue_book(self.book.book_id, self.member.member_id)
        returned = self.txns.return_book(txn.transaction_id, on_date=date.today())
        self.assertEqual(returned.status, "RETURNED")
        self.assertEqual(returned.fine_charged, 0)
        book = self.books.get_book(self.book.book_id)
        self.assertEqual(book.available_copies, 2)

    def test_return_book_overdue_applies_fine(self):
        issue_date = date.today() - timedelta(days=20)
        txn = self.txns.issue_book(self.book.book_id, self.member.member_id, on_date=issue_date)
        returned = self.txns.return_book(txn.transaction_id, on_date=date.today())
        overdue_days = 20 - LOAN_PERIOD_DAYS
        self.assertEqual(returned.fine_charged, overdue_days * FINE_PER_DAY)
        member = self.members.get_member(self.member.member_id)
        self.assertEqual(member.outstanding_fine, overdue_days * FINE_PER_DAY)

    def test_return_already_returned_fails(self):
        txn = self.txns.issue_book(self.book.book_id, self.member.member_id)
        self.txns.return_book(txn.transaction_id)
        with self.assertRaises(BusinessRuleError):
            self.txns.return_book(txn.transaction_id)

    def test_renew_extends_due_date(self):
        txn = self.txns.issue_book(self.book.book_id, self.member.member_id)
        renewed = self.txns.renew_transaction(txn.transaction_id)
        expected = date.today() + timedelta(days=LOAN_PERIOD_DAYS * 2)
        self.assertEqual(renewed.due_date, expected.isoformat())

    def test_list_overdue(self):
        issue_date = date.today() - timedelta(days=LOAN_PERIOD_DAYS + 5)
        self.txns.issue_book(self.book.book_id, self.member.member_id, on_date=issue_date)
        overdue = self.txns.list_overdue()
        self.assertEqual(len(overdue), 1)


if __name__ == "__main__":
    unittest.main()
