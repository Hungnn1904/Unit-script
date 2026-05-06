import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.enrollments.models import Enrollment, EnrollmentStatus, EnrollmentStatusLog
from apps.enrollments import services
from apps.classes.models import Class
from apps.centers.models import Center
from apps.curriculum.models import Subject
from apps.attendance.models import Attendance
from apps.billing.models import BillingEntry, Discount

User = get_user_model()

@pytest.fixture
def setup_base_data():
    """Tạo dữ liệu nền cho các bài test"""
    center = Center.objects.create(name="Trung tâm Test", code="TT01")
    subject = Subject.objects.create(name="Toán", code="MATH01")
    klass = Class.objects.create(name="Lớp Test", code="L01", center=center, subject=subject)
    student = User.objects.create_user(username="student_test", password="123")
    return center, klass, student

@pytest.mark.django_db
class TestEnrollmentModelUnit:
    """Unit tests cho logic nội tại của model Enrollment"""

    def test_ut_mod_01_active_auto_update(self, setup_base_data):
        """UT_MOD_01: Tự động cập nhật trường active dựa trên status"""
        _, klass, student = setup_base_data
        
        # Test ACTIVE status
        enr = Enrollment.objects.create(klass=klass, student=student, status=EnrollmentStatus.ACTIVE)
        assert enr.active is True
        
        # Test CANCELLED status
        enr.status = EnrollmentStatus.CANCELLED
        enr.save()
        assert enr.active is False

    def test_ut_mod_02_sessions_from_payment(self, setup_base_data):
        """UT_MOD_02: Tính số buổi từ số tiền đã đóng"""
        _, klass, student = setup_base_data
        enr = Enrollment(
            klass=klass, 
            student=student, 
            fee_per_session=200000, 
            amount_paid=1000000
        )
        assert enr.sessions_from_payment == 5
        
        # Case đơn giá 0
        enr.fee_per_session = 0
        assert enr.sessions_from_payment == 0

    def test_ut_mod_03_remaining_amount(self, setup_base_data):
        """UT_MOD_03: Tính số tiền còn lại (Remaining Amount)"""
        _, klass, student = setup_base_data
        # Giả lập sessions_remaining = 3
        enr = Enrollment(klass=klass, student=student, fee_per_session=100000)
        enr._sessions_remaining_cache = 3 # Dùng cache để cô lập logic model
        
        assert enr.remaining_amount == 300000


@pytest.mark.django_db
class TestEnrollmentServicesUnit:
    """Unit tests cho các hàm nghiệp vụ trong services.py"""

    def test_ut_srv_01_sessions_from_payment_function(self):
        """UT_SRV_01: Hàm tính số buổi thuần túy"""
        assert services.sessions_from_payment(500000, 100000) == 5
        assert services.sessions_from_payment(0, 100000) == 0
        assert services.sessions_from_payment(500000, 0) == 0

    def test_ut_srv_02_recalc_sessions_consumed(self, setup_base_data):
        """UT_SRV_02: Đếm số buổi đã sử dụng từ điểm danh"""
        _, klass, student = setup_base_data
        enr = Enrollment.objects.create(klass=klass, student=student)
        
        # Giả lập sessions trong apps/class_sessions/models.py (cần import nếu cần, nhưng Attendance có FK session)
        # Để đơn giản, ta mock Attendance. objects.filter
        from apps.class_sessions.models import ClassSession
        session1 = ClassSession.objects.create(klass=klass, date=date.today(), index=1)
        session2 = ClassSession.objects.create(klass=klass, date=date.today() - timedelta(days=1), index=2)
        
        Attendance.objects.create(session=session1, student=student, status="P") # Có mặt
        Attendance.objects.create(session=session2, student=student, status="L") # Muộn (vẫn tính là học)
        
        consumed, delta = services.recalc_sessions_consumed(enr)
        assert consumed == 2
        enr.refresh_from_db()
        assert enr.sessions_consumed == 2

    def test_ut_srv_03_calculate_end_date_no_schedule(self):
        """UT_SRV_03: Tính ngày kết thúc khi không có lịch học (mặc định hàng ngày)"""
        start = date(2024, 1, 1) # Thứ 2
        # 5 buổi học hàng ngày -> kết thúc vào ngày 2024-01-05 (Thứ 6)
        end_date = services.calculate_end_date(start, 5, None)
        assert end_date == date(2024, 1, 5)

    def test_ut_srv_03_calculate_end_date_with_schedule(self, setup_base_data):
        """UT_SRV_03: Tính ngày kết thúc với lịch học cụ thể (Thứ 2, 4)"""
        _, klass, student = setup_base_data
        # Giả sử klass có lịch biểu
        from apps.classes.models import ClassSchedule
        from datetime import time
        ClassSchedule.objects.create(klass=klass, day_of_week=0, start_time=time(8,0), end_time=time(9,30)) # Thứ 2
        ClassSchedule.objects.create(klass=klass, day_of_week=2, start_time=time(8,0), end_time=time(9,30)) # Thứ 4
        
        start = date(2024, 1, 1) # Thứ 2 (buổi 1)
        # Lịch học: T2(1/1), T4(1/3), T2(1/8), T4(1/10)
        end_date = services.calculate_end_date(start, 4, klass)
        assert end_date == date(2024, 1, 10)

    def test_ut_srv_04_record_status_change(self, setup_base_data):
        """UT_SRV_04: Ghi log thay đổi trạng thái"""
        _, klass, student = setup_base_data
        enr = Enrollment.objects.create(klass=klass, student=student, status=EnrollmentStatus.NEW)
        
        services.record_status_change(enr, EnrollmentStatus.ACTIVE, reason="TEST_REASON", note="Test note")
        
        assert enr.status == EnrollmentStatus.ACTIVE
        log = EnrollmentStatusLog.objects.filter(enrollment=enr).first()
        assert log.old_status == EnrollmentStatus.NEW
        assert log.new_status == EnrollmentStatus.ACTIVE
        assert log.reason == "TEST_REASON"

    def test_ut_srv_05_apply_discount(self):
        """UT_SRV_05: Logic áp dụng giảm giá"""
        # Test giảm phần trăm
        d1 = Discount(percent=10, active=True)
        discount_amt, new_price = services.apply_discount(d1, 100000, 10)
        # 100k * 10 = 1tr. Giảm 10% = 100k. Còn 900k/10 = 90k
        assert discount_amt == 100000
        assert new_price == 90000
        
        # Test max_amount
        d2 = Discount(percent=50, max_amount=10000, active=True)
        discount_amt, _ = services.apply_discount(d2, 100000, 1)
        # Giảm 50% của 100k là 50k, nhưng max_amount là 10k
        assert discount_amt == 10000

    def test_ut_srv_07_transfer_enrollment_funds_validation(self, setup_base_data):
        """UT_SRV_07: Ràng buộc khi chuyển phí"""
        _, klass, student = setup_base_data
        enr_a = Enrollment.objects.create(klass=klass, student=student, fee_per_session=100000, amount_paid=500000)
        enr_b = Enrollment.objects.create(klass=klass, student=student, fee_per_session=100000)
        
        # Chuyển quá số dư
        with pytest.raises(ValueError, match="Số tiền chuyển vượt quá số dư hiện có"):
            services.transfer_enrollment_funds(enr_a, enr_b, Decimal('600000'))
            
        # Chuyển tiền không chia hết cho đơn giá
        with pytest.raises(ValueError, match="Số tiền phải chia hết cho đơn giá nguồn"):
            services.transfer_enrollment_funds(enr_a, enr_b, Decimal('150000'))

    def test_ut_srv_07_transfer_funds_db_records(self, setup_base_data):
        """UT_SRV_07: Kiểm tra bản ghi DB sau khi chuyển phí thành công"""
        _, klass, student = setup_base_data
        enr_a = Enrollment.objects.create(klass=klass, student=student, fee_per_session=100000, amount_paid=500000)
        enr_b = Enrollment.objects.create(klass=klass, student=student, fee_per_session=100000, amount_paid=0)
        
        # Giả lập sessions_remaining để pass validation (amount_paid=500k, fee=100k -> 5 buổi)
        # transfer_enrollment_funds dùng source.remaining_amount
        
        services.transfer_enrollment_funds(enr_a, enr_b, Decimal('200000'))
        
        # Kiểm tra BillingEntry
        entry_a = BillingEntry.objects.filter(enrollment=enr_a, amount=-200000).exists()
        entry_b = BillingEntry.objects.filter(enrollment=enr_b, amount=200000).exists()
        assert entry_a is True
        assert entry_b is True
