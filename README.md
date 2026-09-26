# Library Management System

A console-based **Library Management System** built in pure Python (standard
library only). Built as the "Build Your Own Project" submission for the
flipped course evaluation.

It manages the full lifecycle of a library: cataloguing books, registering
members, issuing/returning/renewing loans, calculating overdue fines, and
generating management reports — all backed by a local SQLite database.

## Features

- **Book Management** — add, view, search, update, and delete books, with
  automatic copy-count top-up when the same ISBN is added again.
- **Member Management** — add, view, search, update, and delete members,
  with email/phone validation and membership tiers (STANDARD/PREMIUM/STUDENT).
- **Issue / Return / Renew** — issue a book to a member (enforcing a
  per-member borrow limit and outstanding-fine limit), return it (with
  automatic overdue fine calculation), or renew an on-time loan.
- **Fine Management** — overdue loans accrue a per-day fine automatically on
  return; members can pay down their outstanding balance.
- **Reports & Analytics** — library-wide summary, overdue report, most
  borrowed books, and category distribution.
- **Librarian Authentication** — salted/hashed login required before the
  main menu is shown (default account: `admin` / `admin123`).
- **Logging** — every significant action (logins, issues, returns, errors)
  is written to `logs/library.log`.

## Technologies / Tools Used

- **Python 3.9+** (standard library only — no external runtime dependencies)
- **SQLite3** (`sqlite3` module) for persistent storage
- **unittest** for automated testing
- **Git** for version control

## Project Structure

```
library-management-system/
├── main.py                     # CLI entry point (presentation layer)
├── src/
│   ├── database.py             # SQLite connection + schema (ER design)
│   ├── models.py                # Book / Member / Transaction dataclasses
│   ├── exceptions.py            # Custom exception hierarchy
│   ├── utils.py                  # Validation helpers + logging setup
│   ├── auth.py                    # Librarian authentication (salted hash)
│   ├── book_manager.py             # Module 1: Book CRUD
│   ├── member_manager.py            # Module 2: Member CRUD
│   ├── transaction_manager.py        # Module 3: Issue/Return/Renew + fines
│   └── reports.py                     # Module 4: Reporting & analytics
├── tests/
│   ├── test_book_manager.py
│   ├── test_member_manager.py
│   └── test_transaction_manager.py
├── docs/
│   ├── design.md                # Problem statement, requirements, diagrams
│   └── diagrams/                # Architecture / UML / ER diagrams (PNG)
├── data/                         # SQLite database file (created at runtime)
├── logs/                          # Log file (created at runtime)
├── statement.md
├── requirements.txt
├── .gitignore
└── README.md
```

## Steps to Install & Run

### 1. Prerequisites

- Python 3.9 or later installed (`python3 --version` to check).
- No external packages are required — the project only uses Python's
  standard library, so `requirements.txt` is intentionally empty.

### 2. Clone the repository

```bash
git clone https://github.com/<your-username>/library-management-system.git
cd library-management-system
```

### 3. (Optional) Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

### 4. Run the application

```bash
python3 main.py
```

On first run, the SQLite database is created automatically at
`data/library.db` with a default librarian account:

- **Username:** `admin`
- **Password:** `admin123`

Log in, and you'll see the main menu:

```
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
```

Navigate the numbered menus to add books/members, issue and return loans,
and view reports.

### 5. Reset the data (optional)

To start from a clean database, simply delete `data/library.db` (and
`logs/library.log` if you also want a clean log) — it will be recreated
automatically the next time you run `main.py`.

```bash
rm -f data/library.db logs/library.log
```

## Instructions for Testing

The project includes 26 automated unit tests covering validation rules,
business rules (borrow limits, fine limits, availability), and edge cases,
using an in-memory SQLite database so tests never touch `data/library.db`.

Run the full suite from the project root:

```bash
python3 -m unittest discover -s tests -v
```

Expected output ends with:

```
Ran 26 tests in 0.0Xs

OK
```

## Business Rules Enforced

| Rule | Value |
|---|---|
| Loan period | 14 days |
| Fine per overdue day | Rs. 5.00 |
| Max books issued per member at once | 3 |
| Max outstanding fine before new loans are blocked | Rs. 50.00 |

These constants live at the top of `src/transaction_manager.py` and can be
tuned in one place.

## Screenshots

See `docs/diagrams/` for the architecture, workflow, use case, class,
sequence, and ER diagrams referenced in the project report.

## Further Documentation

- [`docs/design.md`](docs/design.md) — problem statement, functional &
  non-functional requirements, architecture, and all design diagrams.
- [`statement.md`](statement.md) — problem statement, scope, target users,
  and high-level features (as required by the submission guidelines).
