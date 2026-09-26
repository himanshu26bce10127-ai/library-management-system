"""
Cross-cutting utilities: logging configuration and input validation helpers.

Keeping these in one small module avoids duplicating validation logic
across book_manager, member_manager and transaction_manager.
"""

import logging
import os
import re
from datetime import date

from .exceptions import ValidationError

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "library.log")

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$")
ISBN_RE = re.compile(r"^(97(8|9))?\d{9}(\d|X)$")


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger that writes to logs/library.log.

    Centralising configuration here means every module logs consistently
    (same format, same file) without repeating boilerplate, and satisfies
    the 'Logging or monitoring' non-functional requirement.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def require_non_empty(value: str, field_name: str) -> str:
    if value is None or not str(value).strip():
        raise ValidationError(f"{field_name} cannot be empty.")
    return str(value).strip()


def require_positive_int(value, field_name: str) -> int:
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a whole number.")
    if ivalue <= 0:
        raise ValidationError(f"{field_name} must be greater than zero.")
    return ivalue


def validate_year(value, field_name: str = "Publication year") -> int:
    try:
        year = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid year.")
    current_year = date.today().year
    if year < 1450 or year > current_year:
        raise ValidationError(f"{field_name} must be between 1450 and {current_year}.")
    return year


def validate_isbn(value: str) -> str:
    value = require_non_empty(value, "ISBN").replace("-", "").replace(" ", "")
    if not ISBN_RE.match(value):
        raise ValidationError(
            "ISBN must be a valid 10 or 13 digit ISBN (digits, optionally ending in X)."
        )
    return value


def validate_email(value: str) -> str:
    value = require_non_empty(value, "Email")
    if not EMAIL_RE.match(value):
        raise ValidationError(f"'{value}' is not a valid email address.")
    return value


def validate_phone(value: str) -> str:
    value = require_non_empty(value, "Phone number")
    digits = re.sub(r"\D", "", value)
    if len(digits) < 7 or len(digits) > 15:
        raise ValidationError("Phone number must contain 7-15 digits.")
    return value
