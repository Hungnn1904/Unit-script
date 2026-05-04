"""
Unit tests for User model (F-01, F-02, F-03)
- Authentication & RBAC
- User Account Management

Rollback Strategy:
Each test inherits from django.test.TestCase which wraps each test in
transaction.atomic() and rollback after completion. No manual cleanup needed.
"""
import uuid
from django.test import TestCase, TransactionTestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from apps.accounts.models import ParentStudentRelation, UserCodeCounter

User = get_user_model()


class UserModelCreationTests(TransactionTestCase):
    """
    F-01, F-03: Test User model creation and field validation
    Rollback: Each test auto-rolled back via django.test.TestCase
    """

    def test_create_user_valid(self):
        """
        TC_F01_EP_01: Create user with valid data
        Expected: User created in DB, count increases by 1
        """
        initial_count = User.objects.count()
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            role="STUDENT"
        )
        # DB Check: Count increased
        self.assertEqual(User.objects.count(), initial_count + 1)
        # DB Check: User exists by filter
        self.assertTrue(User.objects.filter(username="testuser").exists())
        # Verify object state
        self.assertEqual(user.role, "STUDENT")
        self.assertTrue(user.is_active)

    def test_national_id_unique_constraint(self):
        """
        TC_F03_Constraints_01: national_id field must be unique
        Expected: IntegrityError when inserting duplicate
        DB Check: Only the first user with that national_id exists
        """
        User.objects.create_user(
            username="user1",
            password="pass123",
            national_id="123456789012"
        )
        # Attempt duplicate national_id
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="user2",
                password="pass123",
                national_id="123456789012"
            )
        self.assertEqual(User.objects.filter(national_id="123456789012").count(), 1)
        self.assertFalse(User.objects.filter(username="user2").exists())

    def test_user_code_unique_constraint(self):
        """
        TC_F03_Constraints_02: user_code field must be unique
        Expected: IntegrityError when inserting duplicate
        DB Check: Only the first user with that user_code exists
        """
        User.objects.create_user(
            username="user1",
            password="pass123",
            user_code="UC0001"
        )
        # Attempt duplicate user_code
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="user2",
                password="pass123",
                user_code="UC0001"
            )
        self.assertEqual(User.objects.filter(user_code="UC0001").count(), 1)
        self.assertFalse(User.objects.filter(username="user2").exists())

    def test_username_unique_constraint(self):
        """
        TC_F03_Constraints_03: username field must be unique (inherited)
        Expected: IntegrityError when inserting duplicate
        """
        User.objects.create_user(
            username="unique_user",
            password="pass123"
        )
        # Attempt duplicate username
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="unique_user",
                password="pass123"
            )

    def test_inactive_user_not_logged_in(self):
        """
        TC_F01_EP_02: inactive_user (is_active=False) should be rejected at login
        Expected: User created with is_active=False, confirm in DB
        DB Check: user.is_active == False in DB
        """
        user = User.objects.create_user(
            username="inactive_user",
            password="pass123",
            is_active=False
        )
        # DB Check: Verify is_active state
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_password_hashed_on_create(self):
        """
        TC_F01_EP_03: Password should be hashed, not stored as plaintext
        Expected: password field starts with "pbkdf2" hash prefix, not plaintext
        DB Check: user.password != "plaintext", starts with "pbkdf2"
        """
        user = User.objects.create_user(
            username="testuser",
            password="plaintext_password"
        )
        # DB Check: Password is hashed
        user.refresh_from_db()
        self.assertNotEqual(user.password, "plaintext_password")
        self.assertTrue(user.password.startswith("pbkdf2"))

    def test_default_role_is_student(self):
        """
        TC_F03_Default_01: Default role should be STUDENT if not specified
        Expected: role == "STUDENT"
        DB Check: user.role == "STUDENT" in DB
        NOTE: This is a silent risk - no explicit role set via user creation form
        """
        user = User.objects.create_user(
            username="default_role_user",
            password="pass123"
            # role not specified
        )
        # DB Check: Default role is STUDENT
        user.refresh_from_db()
        self.assertEqual(user.role, "STUDENT")


class UserFieldBoundaryTests(TestCase):
    """
    F-03: Field length boundary value analysis (BVA)
    """

    def test_username_max_length_150(self):
        """
        TC_F03_BVA_Username_150: username max length is 150 chars
        Expected: 150-char username accepted
        DB Check: user.username == 150-char string
        """
        username_150 = "a" * 150
        user = User.objects.create_user(
            username=username_150,
            password="pass123"
        )
        user.refresh_from_db()
        self.assertEqual(user.username, username_150)
        self.assertEqual(len(user.username), 150)

    def test_username_exceeds_max_length_151(self):
        """
        TC_F03_BVA_Username_151: username > 150 chars should fail validation
        Expected: ValidationError on full_clean()
        """
        username_151 = "a" * 151
        user = User(username=username_151, password="pass123")
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_phone_max_length_20(self):
        """
        TC_F03_BVA_Phone_20: phone max length is 20 chars
        Expected: 20-char phone accepted
        DB Check: phone field saved correctly
        """
        phone_20 = "0" + "1" * 19  # 20 chars
        user = User.objects.create_user(
            username="phone_test",
            password="pass123",
            phone=phone_20
        )
        user.refresh_from_db()
        self.assertEqual(user.phone, phone_20)

    def test_phone_exceeds_max_length_21(self):
        """
        TC_F03_BVA_Phone_21: phone > 20 chars should fail
        Expected: ValidationError on full_clean()
        """
        phone_21 = "0" + "1" * 20  # 21 chars
        user = User(
            username="phone_test2",
            password="pass123",
            phone=phone_21
        )
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_national_id_max_length_32(self):
        """
        TC_F03_BVA_NationalID: national_id max length is 32
        Expected: 32-char national_id accepted
        """
        nid_32 = "1" * 32
        user = User.objects.create_user(
            username="nid_test",
            password="pass123",
            national_id=nid_32
        )
        user.refresh_from_db()
        self.assertEqual(len(user.national_id), 32)


class UserCodeCounterTests(TestCase):
    """
    F-03: Test UserCodeCounter utility for auto-generating user codes
    """

    def test_next_code_generates_sequential(self):
        """
        TC_F03_UserCodeCounter_01: next_code() increments counter
        Expected: First call returns prefix0001, second returns prefix0002
        """
        from apps.accounts.models import UserCodeCounter
        
        code1 = UserCodeCounter.next_code("TEST")
        code2 = UserCodeCounter.next_code("TEST")
        
        self.assertEqual(code1, "TEST0001")
        self.assertEqual(code2, "TEST0002")

    def test_next_code_different_prefixes_separate(self):
        """
        TC_F03_UserCodeCounter_02: Different prefixes maintain separate counters
        Expected: TEST0001, PROD0001 (independent counters)
        """
        from apps.accounts.models import UserCodeCounter
        
        code1 = UserCodeCounter.next_code("TEST")
        code2 = UserCodeCounter.next_code("PROD")
        
        self.assertEqual(code1, "TEST0001")
        self.assertEqual(code2, "PROD0001")

    def test_user_code_counter_str_format(self):
        counter = UserCodeCounter.objects.create(prefix="AB", last_number=7)
        self.assertEqual(str(counter), "AB-0007")


class UserDisplayHelperTests(TestCase):
    def test_preferred_full_name_uses_full_name_first(self):
        user = User.objects.create_user(
            username="fullname",
            password="pass123",
            first_name="Nguyen",
            last_name="An",
            email="nguyen@example.com",
        )
        self.assertEqual(user.preferred_full_name(), "Nguyen An")
        self.assertEqual(user.preferred_email(), "nguyen@example.com")
        self.assertEqual(user.display_name_with_email(), "Nguyen An (nguyen@example.com)")

    def test_preferred_full_name_falls_back_to_username(self):
        user = User.objects.create_user(username="fallbackuser", password="pass123")
        self.assertEqual(user.preferred_full_name(), "fallbackuser")
        self.assertEqual(user.preferred_email(), "")
        self.assertEqual(user.display_name_with_email(), "fallbackuser")

    def test_display_name_with_email_returns_email_when_name_missing(self):
        user = User.objects.create_user(username="emailonly", password="pass123", email="only@example.com")
        user.first_name = ""
        user.last_name = ""
        user.username = ""
        self.assertEqual(user.preferred_full_name(), "Chưa cập nhật")
        self.assertEqual(user.display_name_with_email(), "Chưa cập nhật (only@example.com)")


class ParentStudentRelationTests(TestCase):
    def test_relation_string_representation(self):
        parent = User.objects.create_user(username="parent1", password="pass123", role="PARENT")
        student = User.objects.create_user(username="student1", password="pass123", role="STUDENT")
        relation = ParentStudentRelation.objects.create(parent=parent, student=student, note="linked")
        self.assertEqual(str(relation), "parent1 → student1")

    def test_relation_prevents_same_parent_and_student(self):
        user = User.objects.create_user(username="sameuser", password="pass123")
        relation = ParentStudentRelation(parent=user, student=user)
        with self.assertRaises(ValidationError):
            relation.full_clean()
