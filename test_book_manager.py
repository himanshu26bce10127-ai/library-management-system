import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.book_manager import BookManager
from src.database import Database
from src.exceptions import BusinessRuleError, NotFoundError, ValidationError


class TestBookManager(unittest.TestCase):
    def setUp(self):
        # In-memory database keeps each test isolated and fast.
        self.db = Database(db_path=":memory:")
        self.books = BookManager(self.db)

    def tearDown(self):
        self.db.close()

    def test_add_book_success(self):
        book = self.books.add_book(
            isbn="9780134685991",
            title="Effective Java",
            author="Joshua Bloch",
            category="Programming",
            year=2018,
            copies=3,
        )
        self.assertEqual(book.title, "Effective Java")
        self.assertEqual(book.available_copies, 3)
        self.assertEqual(book.total_copies, 3)

    def test_add_book_invalid_isbn_raises(self):
        with self.assertRaises(ValidationError):
            self.books.add_book(
                isbn="123",
                title="Bad ISBN Book",
                author="Author",
                category="Fiction",
                year=2020,
                copies=1,
            )

    def test_add_book_invalid_year_raises(self):
        with self.assertRaises(ValidationError):
            self.books.add_book(
                isbn="9780134685991",
                title="Future Book",
                author="Author",
                category="Fiction",
                year=3000,
                copies=1,
            )

    def test_add_same_isbn_tops_up_copies(self):
        self.books.add_book("9780134685991", "Effective Java", "J. Bloch", "Programming", 2018, 2)
        book = self.books.add_book("9780134685991", "Effective Java", "J. Bloch", "Programming", 2018, 3)
        self.assertEqual(book.total_copies, 5)
        self.assertEqual(book.available_copies, 5)

    def test_get_book_not_found(self):
        with self.assertRaises(NotFoundError):
            self.books.get_book(999)

    def test_search_books(self):
        self.books.add_book("9780134685991", "Effective Java", "Joshua Bloch", "Programming", 2018, 2)
        self.books.add_book("9780132350884", "Clean Code", "Robert Martin", "Programming", 2008, 1)
        results = self.books.search_books("Java")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Effective Java")

    def test_delete_book_with_no_copies_issued(self):
        book = self.books.add_book("9780134685991", "Effective Java", "J. Bloch", "Programming", 2018, 1)
        self.books.delete_book(book.book_id)
        with self.assertRaises(NotFoundError):
            self.books.get_book(book.book_id)

    def test_delete_book_with_copies_issued_fails(self):
        book = self.books.add_book("9780134685991", "Effective Java", "J. Bloch", "Programming", 2018, 1)
        self.books.decrement_availability(book.book_id)  # simulate an active loan
        with self.assertRaises(BusinessRuleError):
            self.books.delete_book(book.book_id)

    def test_decrement_availability_below_zero_fails(self):
        book = self.books.add_book("9780134685991", "Effective Java", "J. Bloch", "Programming", 2018, 1)
        self.books.decrement_availability(book.book_id)
        with self.assertRaises(BusinessRuleError):
            self.books.decrement_availability(book.book_id)


if __name__ == "__main__":
    unittest.main()
