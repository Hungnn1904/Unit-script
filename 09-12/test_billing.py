from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from apps.accounts.models import User
from apps.centers.models import Center
from apps.curriculum.models import Subject
from apps.classes.models import Class
from apps.enrollments.models import Enrollment, EnrollmentStatus
from apps.billing.models import Discount, BillingEntry
from apps.enrollments.services import apply_discount, create_purchase_entry

class BillingUnitTests(TestCase):
    def setUp(self):
        self.center = Center.objects.create(name="Billing Center")
        self.subject = Subject.objects.create(name="Billing Subject")
        self.student = User.objects.create_user(username="bill_student", role="STUDENT")
        self.klass = Class.objects.create(
            code="BILL_01", name="Bill Class",
            center=self.center, subject=self.subject
        )
        self.enrollment = Enrollment.objects.create(
            klass=self.klass, student=self.student, status=EnrollmentStatus.ACTIVE,
            fee_per_session=300000, sessions_purchased=10
        )

    def test_tc_f12_dt_01_valid_discount(self):
        """TC_F12_DT_01: Active discount, within date, usage_count < limit."""
        discount = Discount.objects.create(
            code="SAVE10", name="10% Off", percent=10, 
            active=True, usage_limit=10, usage_count=0
        )
        discount_amount, new_unit_price = apply_discount(discount, 300000, 5)
        # 10% of (300,000 * 5 = 1,500,000) is 150,000
        self.assertEqual(discount_amount, 150000)
        # effective total = 1,350,000. unit_price = 1,350,000 / 5 = 270,000
        self.assertEqual(new_unit_price, 270000)

    def test_tc_f12_dt_02_expired_discount(self):
        """TC_F12_DT_02: Expired discount (end_date < today)."""
        discount = Discount.objects.create(
            code="EXPIRED", name="Expired", percent=20, 
            active=True, end_date=date.today() - timedelta(days=1)
        )
        discount_amount, new_unit_price = apply_discount(discount, 300000, 5)
        self.assertEqual(discount_amount, 0)
        self.assertEqual(new_unit_price, 300000)

    def test_tc_f12_dt_03_usage_limit_reached(self):
        """TC_F12_DT_03: Discount with usage_count = usage_limit."""
        discount = Discount.objects.create(
            code="LIMIT", name="At Limit", percent=20, 
            active=True, usage_limit=2, usage_count=2
        )
        discount_amount, new_unit_price = apply_discount(discount, 300000, 5)
        self.assertEqual(discount_amount, 0)
        self.assertEqual(new_unit_price, 300000)

    def test_tc_f12_dt_05_max_amount_cap(self):
        """TC_F12_DT_05: Discount with max_amount cap."""
        discount = Discount.objects.create(
            code="CAP", name="Capped", percent=50, 
            active=True, max_amount=200000
        )
        # 50% of (300,000 * 10 = 3,000,000) is 1,500,000, but capped at 200,000
        discount_amount, new_unit_price = apply_discount(discount, 300000, 10)
        self.assertEqual(discount_amount, 200000)
        # effective total = 2,800,000. unit price = 280,000
        self.assertEqual(new_unit_price, 280000)

    def test_tc_f12_bva_03_percent_above_100(self):
        """TC_F12_BVA_03: Discount percent = 101 rejected."""
        discount = Discount(code="OVER", percent=101)
        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_usage_count_increments(self):
        """Verify that usage_count increments when create_purchase_entry is called with a discount."""
        discount = Discount.objects.create(
            code="PROMO", name="Promo", percent=10, 
            active=True, usage_limit=10, usage_count=0
        )
        create_purchase_entry(self.enrollment, discount=discount, force=True)
        discount.refresh_from_db()
        self.assertEqual(discount.usage_count, 1)

    def test_usage_count_not_incremented_if_discount_not_applied(self):
        """Verify that usage_count does NOT increment if discount is invalid."""
        discount = Discount.objects.create(
            code="INVALID", name="Invalid", percent=10, 
            active=False, usage_limit=10, usage_count=0
        )
        create_purchase_entry(self.enrollment, discount=discount, force=True)
        discount.refresh_from_db()
        self.assertEqual(discount.usage_count, 0)
