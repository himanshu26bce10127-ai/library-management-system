import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Database
from src.exceptions import BusinessRuleError, NotFoundError, ValidationError
from src.member_manager import MemberManager


class TestMemberManager(unittest.TestCase):
    def setUp(self):
        self.db = Database(db_path=":memory:")
        self.members = MemberManager(self.db)

    def tearDown(self):
        self.db.close()

    def test_add_member_success(self):
        m = self.members.add_member("Asha Rao", "asha@example.com", "9876543210", "STUDENT")
        self.assertEqual(m.name, "Asha Rao")
        self.assertEqual(m.membership_type, "STUDENT")
        self.assertEqual(m.outstanding_fine, 0)

    def test_add_member_invalid_email_raises(self):
        with self.assertRaises(ValidationError):
            self.members.add_member("Bad Email", "not-an-email", "9876543210")

    def test_add_member_duplicate_email_raises(self):
        self.members.add_member("Asha Rao", "asha@example.com", "9876543210")
        with self.assertRaises(ValidationError):
            self.members.add_member("Asha Duplicate", "asha@example.com", "9876543211")

    def test_add_member_invalid_membership_type_raises(self):
        with self.assertRaises(ValidationError):
            self.members.add_member("Test User", "test@example.com", "9876543210", "GOLD")

    def test_get_member_not_found(self):
        with self.assertRaises(NotFoundError):
            self.members.get_member(999)

    def test_update_member(self):
        m = self.members.add_member("Asha Rao", "asha@example.com", "9876543210")
        updated = self.members.update_member(m.member_id, phone="9999999999")
        self.assertEqual(updated.phone, "9999999999")

    def test_pay_fine_reduces_outstanding(self):
        m = self.members.add_member("Asha Rao", "asha@example.com", "9876543210")
        self.members.add_fine(m.member_id, 25.0)
        updated = self.members.pay_fine(m.member_id, 10.0)
        self.assertAlmostEqual(updated.outstanding_fine, 15.0)

    def test_pay_fine_more_than_owed_fails(self):
        m = self.members.add_member("Asha Rao", "asha@example.com", "9876543210")
        self.members.add_fine(m.member_id, 5.0)
        with self.assertRaises(BusinessRuleError):
            self.members.pay_fine(m.member_id, 10.0)

    def test_delete_member_with_unpaid_fine_fails(self):
        m = self.members.add_member("Asha Rao", "asha@example.com", "9876543210")
        self.members.add_fine(m.member_id, 10.0)
        with self.assertRaises(BusinessRuleError):
            self.members.delete_member(m.member_id)


if __name__ == "__main__":
    unittest.main()
