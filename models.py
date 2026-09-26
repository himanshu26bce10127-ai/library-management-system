"""
Lightweight data model classes.

These are plain dataclasses used to move structured data between the
database layer and the manager/report layers, instead of passing raw
sqlite3.Row objects around everywhere.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Book:
    book_id: int
    isbn: str
    title: str
    author: str
    category: str
    year: int
    total_copies: int
    available_copies: int

    @classmethod
    def from_row(cls, row) -> "Book":
        return cls(
            book_id=row["book_id"],
            isbn=row["isbn"],
            title=row["title"],
            author=row["author"],
            category=row["category"],
            year=row["year"],
            total_copies=row["total_copies"],
            available_copies=row["available_copies"],
        )

    def __str__(self) -> str:
        return (
            f"[{self.book_id}] '{self.title}' by {self.author} "
            f"({self.year}) | {self.category} | "
            f"Available: {self.available_copies}/{self.total_copies} | ISBN: {self.isbn}"
        )


@dataclass
class Member:
    member_id: int
    name: str
    email: str
    phone: str
    membership_type: str
    outstanding_fine: float

    @classmethod
    def from_row(cls, row) -> "Member":
        return cls(
            member_id=row["member_id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            membership_type=row["membership_type"],
            outstanding_fine=row["outstanding_fine"],
        )

    def __str__(self) -> str:
        return (
            f"[{self.member_id}] {self.name} | {self.membership_type} | "
            f"{self.email} | {self.phone} | Outstanding fine: Rs.{self.outstanding_fine:.2f}"
        )


@dataclass
class Transaction:
    transaction_id: int
    book_id: int
    member_id: int
    issue_date: str
    due_date: str
    return_date: Optional[str]
    fine_charged: float
    status: str

    @classmethod
    def from_row(cls, row) -> "Transaction":
        return cls(
            transaction_id=row["transaction_id"],
            book_id=row["book_id"],
            member_id=row["member_id"],
            issue_date=row["issue_date"],
            due_date=row["due_date"],
            return_date=row["return_date"],
            fine_charged=row["fine_charged"],
            status=row["status"],
        )

    def __str__(self) -> str:
        ret = self.return_date or "-"
        return (
            f"[Txn {self.transaction_id}] Book {self.book_id} <-> Member {self.member_id} | "
            f"Issued: {self.issue_date} | Due: {self.due_date} | Returned: {ret} | "
            f"Status: {self.status} | Fine: Rs.{self.fine_charged:.2f}"
        )
