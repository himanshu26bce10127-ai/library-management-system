"""
Member Management module (Functional Module 2).

Provides CRUD operations for library members.
"""

from typing import List

from .database import Database
from .exceptions import BusinessRuleError, NotFoundError, ValidationError
from .models import Member
from .utils import get_logger, require_non_empty, validate_email, validate_phone

logger = get_logger(__name__)

VALID_MEMBERSHIP_TYPES = {"STANDARD", "PREMIUM", "STUDENT"}


class MemberManager:
    def __init__(self, db: Database):
        self.db = db

    # ---------- Create ----------
    def add_member(
        self, name: str, email: str, phone: str, membership_type: str = "STANDARD"
    ) -> Member:
        name = require_non_empty(name, "Name")
        email = validate_email(email)
        phone = validate_phone(phone)
        membership_type = membership_type.strip().upper() or "STANDARD"
        if membership_type not in VALID_MEMBERSHIP_TYPES:
            raise ValidationError(
                f"Membership type must be one of {sorted(VALID_MEMBERSHIP_TYPES)}."
            )

        existing = self.db.query_one("SELECT 1 FROM members WHERE email = ?", (email,))
        if existing:
            raise ValidationError(f"A member with email '{email}' already exists.")

        cur = self.db.execute(
            """INSERT INTO members (name, email, phone, membership_type, outstanding_fine)
               VALUES (?, ?, ?, ?, 0)""",
            (name, email, phone, membership_type),
        )
        logger.info("Added new member '%s' (%s).", name, email)
        return self.get_member(cur.lastrowid)

    # ---------- Read ----------
    def get_member(self, member_id: int) -> Member:
        row = self.db.query_one("SELECT * FROM members WHERE member_id = ?", (member_id,))
        if row is None:
            raise NotFoundError(f"No member found with ID {member_id}.")
        return Member.from_row(row)

    def list_members(self) -> List[Member]:
        rows = self.db.query_all("SELECT * FROM members ORDER BY name")
        return [Member.from_row(r) for r in rows]

    def search_members(self, keyword: str) -> List[Member]:
        keyword = require_non_empty(keyword, "Search keyword")
        like = f"%{keyword}%"
        rows = self.db.query_all(
            "SELECT * FROM members WHERE name LIKE ? OR email LIKE ? ORDER BY name",
            (like, like),
        )
        return [Member.from_row(r) for r in rows]

    # ---------- Update ----------
    def update_member(self, member_id: int, **fields) -> Member:
        self.get_member(member_id)  # raises NotFoundError if missing
        allowed = {"name", "email", "phone", "membership_type"}
        updates = {}
        for key, value in fields.items():
            if key not in allowed or value in (None, ""):
                continue
            if key == "email":
                value = validate_email(value)
            elif key == "phone":
                value = validate_phone(value)
            elif key == "membership_type":
                value = value.strip().upper()
                if value not in VALID_MEMBERSHIP_TYPES:
                    raise ValidationError(
                        f"Membership type must be one of {sorted(VALID_MEMBERSHIP_TYPES)}."
                    )
            else:
                value = require_non_empty(value, key)
            updates[key] = value

        if not updates:
            return self.get_member(member_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = tuple(updates.values()) + (member_id,)
        self.db.execute(f"UPDATE members SET {set_clause} WHERE member_id = ?", params)
        logger.info("Updated member %d: %s", member_id, updates)
        return self.get_member(member_id)

    # ---------- Delete ----------
    def delete_member(self, member_id: int) -> None:
        member = self.get_member(member_id)
        active = self.db.query_one(
            "SELECT 1 FROM transactions WHERE member_id = ? AND status = 'ISSUED'",
            (member_id,),
        )
        if active:
            raise BusinessRuleError(
                "Cannot delete a member who currently has books issued to them."
            )
        if member.outstanding_fine > 0:
            raise BusinessRuleError(
                "Cannot delete a member with an unpaid outstanding fine."
            )
        self.db.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
        logger.info("Deleted member %d ('%s').", member_id, member.name)

    # ---------- Fine helpers used by TransactionManager ----------
    def add_fine(self, member_id: int, amount: float) -> None:
        self.db.execute(
            "UPDATE members SET outstanding_fine = outstanding_fine + ? WHERE member_id = ?",
            (amount, member_id),
        )

    def pay_fine(self, member_id: int, amount: float) -> Member:
        member = self.get_member(member_id)
        if amount <= 0:
            raise ValidationError("Payment amount must be greater than zero.")
        if amount > member.outstanding_fine:
            raise BusinessRuleError(
                f"Payment (Rs.{amount:.2f}) exceeds outstanding fine "
                f"(Rs.{member.outstanding_fine:.2f})."
            )
        self.db.execute(
            "UPDATE members SET outstanding_fine = outstanding_fine - ? WHERE member_id = ?",
            (amount, member_id),
        )
        logger.info("Member %d paid fine of Rs.%.2f.", member_id, amount)
        return self.get_member(member_id)
