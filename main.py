#!/usr/bin/env python3
"""
Library Management System - Command Line Interface.

Run with:  python main.py

This is the presentation layer only: it collects input, calls into the
manager classes in src/, and prints results. All validation and business
logic lives in the manager modules so it can be unit tested independently
of the CLI.
"""

import sys
from datetime import date

from src.auth import AuthManager
from src.book_manager import BookManager
from src.database import Database
from src.exceptions import LibraryError
from src.member_manager import MemberManager
from src.reports import ReportManager
from src.transaction_manager import TransactionManager
from src.utils import get_logger

logger = get_logger("main")


def prompt(label: str) -> str:
    return input(f"  {label}: ").strip()


def pause():
    input("\nPress Enter to continue...")


# --------------------------------------------------------------------------
# Menus
# --------------------------------------------------------------------------
MAIN_MENU = """
==================================================
   LIBRARY MANAGEMENT SYSTEM
==================================================
 1. Book Management
 2. Member Management
 3. Issue / Return / Renew Books
 4. Reports & Analytics
 5. Pay Member Fine
 0. Exit
==================================================
"""

BOOK_MENU = """
--- Book Management ---
 1. Add Book
 2. View All Books
 3. Search Books
 4. Update Book
 5. Delete Book
 0. Back
"""

MEMBER_MENU = """
--- Member Management ---
 1. Add Member
 2. View All Members
 3. Search Members
 4. Update Member
 5. Delete Member
 0. Back
"""

TXN_MENU = """
--- Issue / Return / Renew ---
 1. Issue Book
 2. Return Book
 3. Renew Book
 4. View Member's Active Loans
 5. View All Transactions
 0. Back
"""

REPORT_MENU = """
--- Reports & Analytics ---
 1. Library Summary
 2. Overdue Books Report
 3. Most Borrowed Books
 4. Category Distribution
 0. Back
"""


def book_menu(books: BookManager):
    while True:
        print(BOOK_MENU)
        choice = prompt("Choose an option")
        try:
            if choice == "1":
                book = books.add_book(
                    isbn=prompt("ISBN"),
                    title=prompt("Title"),
                    author=prompt("Author"),
                    category=prompt("Category"),
                    year=prompt("Publication year"),
                    copies=prompt("Number of copies"),
                )
                print(f"\n✔ Added: {book}")
            elif choice == "2":
                all_books = books.list_books()
                print(f"\n{len(all_books)} book(s) in catalogue:")
                for b in all_books:
                    print(" ", b)
            elif choice == "3":
                results = books.search_books(prompt("Search keyword (title/author/category/isbn)"))
                print(f"\n{len(results)} result(s):")
                for b in results:
                    print(" ", b)
            elif choice == "4":
                book_id = int(prompt("Book ID to update"))
                field = prompt("Field to update (title/author/category/year/total_copies)")
                value = prompt("New value")
                updated = books.update_book(book_id, **{field: value})
                print(f"\n✔ Updated: {updated}")
            elif choice == "5":
                book_id = int(prompt("Book ID to delete"))
                books.delete_book(book_id)
                print("\n✔ Book deleted.")
            elif choice == "0":
                return
            else:
                print("Invalid option.")
        except (LibraryError, ValueError) as e:
            print(f"\n✘ Error: {e}")
        pause()


def member_menu(members: MemberManager):
    while True:
        print(MEMBER_MENU)
        choice = prompt("Choose an option")
        try:
            if choice == "1":
                m = members.add_member(
                    name=prompt("Name"),
                    email=prompt("Email"),
                    phone=prompt("Phone"),
                    membership_type=prompt("Membership type (STANDARD/PREMIUM/STUDENT)") or "STANDARD",
                )
                print(f"\n✔ Added: {m}")
            elif choice == "2":
                for m in members.list_members():
                    print(" ", m)
            elif choice == "3":
                for m in members.search_members(prompt("Search keyword (name/email)")):
                    print(" ", m)
            elif choice == "4":
                member_id = int(prompt("Member ID to update"))
                field = prompt("Field to update (name/email/phone/membership_type)")
                value = prompt("New value")
                updated = members.update_member(member_id, **{field: value})
                print(f"\n✔ Updated: {updated}")
            elif choice == "5":
                member_id = int(prompt("Member ID to delete"))
                members.delete_member(member_id)
                print("\n✔ Member deleted.")
            elif choice == "0":
                return
            else:
                print("Invalid option.")
        except (LibraryError, ValueError) as e:
            print(f"\n✘ Error: {e}")
        pause()


def transaction_menu(txns: TransactionManager):
    while True:
        print(TXN_MENU)
        choice = prompt("Choose an option")
        try:
            if choice == "1":
                t = txns.issue_book(int(prompt("Book ID")), int(prompt("Member ID")))
                print(f"\n✔ Issued: {t}")
            elif choice == "2":
                t = txns.return_book(int(prompt("Transaction ID")))
                print(f"\n✔ Returned: {t}")
                if t.fine_charged > 0:
                    print(f"  ⚠ Fine of Rs.{t.fine_charged:.2f} added to member's account.")
            elif choice == "3":
                t = txns.renew_transaction(int(prompt("Transaction ID")))
                print(f"\n✔ Renewed: {t}")
            elif choice == "4":
                for t in txns.list_active_for_member(int(prompt("Member ID"))):
                    print(" ", t)
            elif choice == "5":
                for t in txns.list_all():
                    print(" ", t)
            elif choice == "0":
                return
            else:
                print("Invalid option.")
        except (LibraryError, ValueError) as e:
            print(f"\n✘ Error: {e}")
        pause()


def report_menu(reports: ReportManager):
    while True:
        print(REPORT_MENU)
        choice = prompt("Choose an option")
        try:
            if choice == "1":
                summary = reports.library_summary()
                print("\n--- Library Summary ---")
                for k, v in summary.items():
                    print(f"  {k.replace('_', ' ').title()}: {v}")
            elif choice == "2":
                overdue = reports.overdue_report()
                print(f"\n{len(overdue)} overdue loan(s):")
                for row in overdue:
                    print(
                        f"  Txn {row['transaction_id']} | '{row['book_title']}' | "
                        f"{row['member_name']} ({row['member_email']}) | "
                        f"Due {row['due_date']} | {row['days_overdue']} day(s) overdue | "
                        f"Est. fine Rs.{row['estimated_fine']:.2f}"
                    )
            elif choice == "3":
                for title, count in reports.most_borrowed_books():
                    print(f"  {title}: borrowed {count} time(s)")
            elif choice == "4":
                for category, count in reports.category_distribution():
                    print(f"  {category}: {count} title(s)")
            elif choice == "0":
                return
            else:
                print("Invalid option.")
        except (LibraryError, ValueError) as e:
            print(f"\n✘ Error: {e}")
        pause()


def login(auth: AuthManager) -> bool:
    print("Librarian Login (default: admin / admin123)")
    for _ in range(3):
        username = prompt("Username")
        password = prompt("Password")
        try:
            auth.login(username, password)
            print(f"\n✔ Welcome, {username}!\n")
            return True
        except LibraryError as e:
            print(f"✘ {e}\n")
    print("Too many failed attempts. Exiting.")
    return False


def main():
    db = Database()
    auth = AuthManager(db)
    books = BookManager(db)
    members = MemberManager(db)
    txns = TransactionManager(db, books, members)
    reports = ReportManager(db, txns)

    logger.info("Application started.")

    if not login(auth):
        sys.exit(1)

    try:
        while True:
            print(MAIN_MENU)
            choice = prompt("Choose an option")
            if choice == "1":
                book_menu(books)
            elif choice == "2":
                member_menu(members)
            elif choice == "3":
                transaction_menu(txns)
            elif choice == "4":
                report_menu(reports)
            elif choice == "5":
                try:
                    member_id = int(prompt("Member ID"))
                    amount = float(prompt("Payment amount"))
                    m = members.pay_fine(member_id, amount)
                    print(f"\n✔ Fine updated: {m}")
                except (LibraryError, ValueError) as e:
                    print(f"\n✘ Error: {e}")
                pause()
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid option.")
    finally:
        db.close()
        logger.info("Application closed.")


if __name__ == "__main__":
    main()
