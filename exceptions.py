"""
Custom exception hierarchy for the Library Management System.

Using dedicated exception types (instead of generic Exception/ValueError
everywhere) makes error handling in the CLI layer precise and makes the
intent of each failure obvious in logs and tests.
"""


class LibraryError(Exception):
    """Base class for all application-specific errors."""


class ValidationError(LibraryError):
    """Raised when user-supplied data fails validation rules."""


class NotFoundError(LibraryError):
    """Raised when a requested Book/Member/Transaction does not exist."""


class BusinessRuleError(LibraryError):
    """Raised when an operation violates a business rule.

    Examples: issuing a book with zero copies available, a member with
    unpaid fines trying to borrow another book, returning a book that
    was never issued, etc.
    """


class AuthenticationError(LibraryError):
    """Raised when librarian login credentials are invalid."""
