# Problem Statement

## Problem Statement

Small and medium-sized libraries (school, college, or community libraries)
often still track book inventory, member records, and borrowing activity
using registers or disconnected spreadsheets. This makes it difficult to
know, at a glance, which copies of a book are available, which members
currently hold books, which loans are overdue, and how much in fines is
outstanding across the membership. Manual tracking is slow, error-prone
(duplicate entries, lost records), and offers no easy way to generate
reports for decision-making (e.g., which books are most popular, or which
members need a reminder).

## Scope of the Project

This project delivers a **console-based Library Management System** that
digitizes the core day-to-day operations of a small library:

- Maintaining a catalogue of books (with multiple copies per title).
- Registering and maintaining member records.
- Issuing books to members and processing returns, including automatic
  overdue-fine calculation.
- Renewing loans that are not yet overdue.
- Producing basic operational reports (summary statistics, overdue list,
  most-borrowed titles, category distribution).

Out of scope for this version: a web/GUI front-end, multi-library
(branch) support, email/SMS notifications, and online payment integration
for fines — these are noted as future enhancements in the project report.

## Target Users

- **Librarians / library staff**, who use the system daily to catalogue
  new books, register members, and process issues/returns at the circulation
  desk.
- **Library administrators**, who use the reporting module to review
  usage statistics and outstanding fines.

(The system is single-role in this version — every authenticated user is
treated as a librarian with full access — see "Future Enhancements" in the
project report for a proposed member self-service role.)

## High-Level Features

1. **Book Management** — add, search, update, and delete book records;
   automatically tracks total vs. available copies per title.
2. **Member Management** — add, search, update, and delete member records;
   tracks membership tier and outstanding fine balance.
3. **Circulation (Issue / Return / Renew)** — enforces borrowing rules
   (max active loans per member, outstanding-fine limit) and calculates
   overdue fines automatically on return.
4. **Reports & Analytics** — library-wide summary, overdue report, most
   borrowed books, and category distribution, generated on demand from the
   live database.
5. **Authentication & Logging** — salted/hashed librarian login and a
   persistent activity log (`logs/library.log`) for auditability.
