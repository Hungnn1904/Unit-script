"""
Test map for this file:

1.4 EnrollStudentView.post (UT_ENR_01..UT_ENR_06)
- Decision Table theo class status
- Gom duplicate enrollment va invalid-id negative paths
- File nay dung de chay va chup ket qua phan 1.4 trong bao cao
"""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.classes.models import Class
from apps.enrollments.models import Enrollment, EnrollmentStatus


User = get_user_model()


@pytest.mark.django_db
def test_ut_enr_01_enroll_ongoing_class(auth_client, center, subject):
    """
    UT_ENR_01 - Decision Table: Class Ongoing x New Student -> Allow
    """
    class_obj = Class.objects.create(
        code="CL-ENR-01",
        name="Lop Dang Dien Ra",
        center=center,
        subject=subject,
        status="ONGOING",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    student = User.objects.create_user(
        username="student_a",
        email="a@test.com",
        password="student123",
        role="STUDENT",
    )

    response = auth_client.post(
        reverse("enrollments:create"),
        {
            "student": student.pk,
            "klass": class_obj.pk,
            "status": EnrollmentStatus.NEW,
            "start_date": "2026-04-10",
            "fee_per_session": "300000",
            "sessions_purchased": "10",
            "amount_paid": "0",
            "note": "",
        },
    )

    assert response.status_code == 302, f"Expected 302, got {response.status_code}"
    assert Enrollment.objects.filter(klass=class_obj, student=student).exists(), "Enrollment row should be created"


@pytest.mark.django_db
def test_ut_enr_02_enroll_cancelled_class(auth_client, center, subject):
    """
    UT_ENR_02 - Decision Table: Class Cancelled x Any -> Deny
    """
    class_obj = Class.objects.create(
        code="CL-ENR-02",
        name="Lop Da Huy",
        center=center,
        subject=subject,
        status="CANCELLED",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    student = User.objects.create_user(
        username="student_b",
        email="b@test.com",
        password="student123",
        role="STUDENT",
    )
    count_before = Enrollment.objects.count()

    response = auth_client.post(
        reverse("enrollments:create"),
        {
            "student": student.pk,
            "klass": class_obj.pk,
            "status": EnrollmentStatus.NEW,
            "start_date": "2026-04-10",
            "fee_per_session": "300000",
            "sessions_purchased": "10",
            "amount_paid": "0",
            "note": "",
        },
    )

    status_denied = response.status_code != 302
    has_deny_message = "khong the ghi danh" in response.content.decode("utf-8", errors="ignore").lower()
    count_unchanged = Enrollment.objects.count() == count_before
    assert all([status_denied, has_deny_message, count_unchanged]), (
        "Expected cancelled class to be denied with message and unchanged enrollment count"
    )


@pytest.mark.django_db
def test_ut_enr_03_duplicate_enrollment(auth_client, center, subject):
    """
    UT_ENR_03 - Negative: Duplicate enrollment -> Reject
    """
    class_obj = Class.objects.create(
        code="CL-ENR-03",
        name="Lop Test Duplicate",
        center=center,
        subject=subject,
        status="ONGOING",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    student = User.objects.create_user(
        username="student_c",
        email="c@test.com",
        password="student123",
        role="STUDENT",
    )

    Enrollment.objects.create(
        klass=class_obj,
        student=student,
        status=EnrollmentStatus.NEW,
        fee_per_session=300000,
        sessions_purchased=10,
        amount_paid=0,
        start_date=date(2026, 1, 1),
    )

    response = auth_client.post(
        reverse("enrollments:create"),
        {
            "student": student.pk,
            "klass": class_obj.pk,
            "status": EnrollmentStatus.NEW,
            "start_date": "2026-04-10",
            "fee_per_session": "300000",
            "sessions_purchased": "10",
            "amount_paid": "0",
            "note": "",
        },
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "Học viên này đã có ghi danh đang hoạt động trong lớp." in response.content.decode("utf-8", errors="ignore")
    assert Enrollment.objects.filter(klass=class_obj, student=student).count() == 1, (
        "Only one enrollment should exist for class/student pair"
    )


@pytest.mark.django_db
def test_ut_enr_04_enroll_planned_class(auth_client, center, subject):
    """
    UT_ENR_04 - Decision Table: Class Planned x New Student -> Allow
    """
    class_obj = Class.objects.create(
        code="CL-ENR-04",
        name="Lop Sap Khai Giang",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    student = User.objects.create_user(
        username="student_d",
        email="d@test.com",
        password="student123",
        role="STUDENT",
    )

    response = auth_client.post(
        reverse("enrollments:create"),
        {
            "student": student.pk,
            "klass": class_obj.pk,
            "status": EnrollmentStatus.NEW,
            "start_date": "2026-04-10",
            "fee_per_session": "300000",
            "sessions_purchased": "10",
            "amount_paid": "0",
            "note": "",
        },
    )

    assert response.status_code == 302, f"Expected 302, got {response.status_code}"
    assert Enrollment.objects.filter(klass=class_obj, student=student).exists()


@pytest.mark.django_db
def test_ut_enr_05_enroll_completed_class(auth_client, center, subject):
    """
    UT_ENR_05 - Decision Table: Class Completed x New Student -> Deny
    """
    class_obj = Class.objects.create(
        code="CL-ENR-05",
        name="Lop Da Ket Thuc",
        center=center,
        subject=subject,
        status="COMPLETED",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    student = User.objects.create_user(
        username="student_e",
        email="e@test.com",
        password="student123",
        role="STUDENT",
    )
    count_before = Enrollment.objects.count()

    response = auth_client.post(
        reverse("enrollments:create"),
        {
            "student": student.pk,
            "klass": class_obj.pk,
            "status": EnrollmentStatus.NEW,
            "start_date": "2026-04-10",
            "fee_per_session": "300000",
            "sessions_purchased": "10",
            "amount_paid": "0",
            "note": "",
        },
    )

    status_denied = response.status_code != 302
    has_deny_message = "khong the ghi danh" in response.content.decode("utf-8", errors="ignore").lower()
    count_unchanged = Enrollment.objects.count() == count_before
    assert all([status_denied, has_deny_message, count_unchanged]), (
        "Expected completed class to be denied with message and unchanged enrollment count"
    )


@pytest.mark.django_db
def test_ut_enr_06_enroll_invalid_ids(auth_client, center, subject):
    """
    UT_ENR_06 - Negative Testing: non-existent student id
    """
    class_obj = Class.objects.create(
        code="CL-ENR-06",
        name="Lop Test Loi ID",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    count_before = Enrollment.objects.count()

    response = auth_client.post(
        reverse("enrollments:create"),
        {
            "student": 99999,
            "klass": class_obj.pk,
            "status": EnrollmentStatus.NEW,
            "start_date": "2026-04-10",
            "fee_per_session": "300000",
            "sessions_purchased": "10",
            "amount_paid": "0",
            "note": "",
        },
    )

    assert response.status_code in [200, 400, 404, 422], f"Expected error status, got {response.status_code}"
    assert Enrollment.objects.count() == count_before, "No invalid enrollment row should be created"


@pytest.mark.django_db
def test_add_sec3_enrollment_list_htmx_and_normal(auth_client):
    response_normal = auth_client.get(reverse("enrollments:list"))
    assert response_normal.status_code == 200

    response_htmx = auth_client.get(reverse("enrollments:list"), HTTP_HX_REQUEST="true")
    assert response_htmx.status_code == 200


@pytest.mark.django_db
def test_add_sec3_enrollment_calculate_end_date_invalid(auth_client):
    response = auth_client.get(reverse("enrollments:calculate_end_date"))
    assert response.status_code == 200
    assert response.json() == {"end_date": None}


@pytest.mark.django_db
def test_add_sec3_enrollment_create_get_and_invalid_htmx(auth_client):
    response_get = auth_client.get(reverse("enrollments:create"))
    assert response_get.status_code == 200

    response_invalid = auth_client.post(reverse("enrollments:create"), data={}, HTTP_HX_REQUEST="true")
    assert response_invalid.status_code == 422
    assert "HX-Trigger" in response_invalid


@pytest.mark.django_db
def test_add_sec3_enrollment_create_success(auth_client, center, subject):
    klass = Class.objects.create(code="ADD-ENR-01", name="Enrollment OK", center=center, subject=subject, status="PLANNED")
    student = User.objects.create_user(
        username="add_student_01",
        email="add_student_01@test.com",
        password="student123",
        role="STUDENT",
    )

    response = auth_client.post(
        reverse("enrollments:create"),
        {
            "student": student.pk,
            "klass": klass.pk,
            "status": EnrollmentStatus.NEW,
            "start_date": "2026-04-10",
            "fee_per_session": "300000",
            "sessions_purchased": "10",
            "amount_paid": "0",
            "note": "",
        },
    )

    assert response.status_code == 302
    assert Enrollment.objects.filter(klass=klass, student=student).exists()


@pytest.mark.django_db
def test_add_sec3_enrollment_create_success_second_student(auth_client, center, subject):
    klass = Class.objects.create(code="ADD-ENR-02", name="Enrollment OK 2", center=center, subject=subject, status="PLANNED")
    student = User.objects.create_user(
        username="add_student_02",
        email="add_student_02@test.com",
        password="student123",
        role="STUDENT",
    )

    response = auth_client.post(
        reverse("enrollments:create"),
        {
            "student": student.pk,
            "klass": klass.pk,
            "status": EnrollmentStatus.NEW,
            "start_date": "2026-04-12",
            "fee_per_session": "300000",
            "sessions_purchased": "8",
            "amount_paid": "0",
            "note": "",
        },
    )

    assert response.status_code == 302
    assert Enrollment.objects.filter(klass=klass, student=student).exists()


@pytest.mark.django_db
def test_add_sec3_enrollment_list_contains_created_code(auth_client, center, subject):
    klass = Class.objects.create(code="ADD-ENR-03", name="List Check", center=center, subject=subject, status="PLANNED")
    student = User.objects.create_user(
        username="add_student_03",
        email="add_student_03@test.com",
        password="student123",
        role="STUDENT",
    )
    Enrollment.objects.create(
        klass=klass,
        student=student,
        status=EnrollmentStatus.NEW,
        fee_per_session=300000,
        sessions_purchased=5,
        amount_paid=0,
        start_date=date(2026, 4, 10),
    )

    response = auth_client.get(reverse("enrollments:list"))
    assert response.status_code == 200
    assert "ADD-ENR-03" in response.content.decode("utf-8", errors="ignore")


@pytest.mark.django_db
def test_add_sec3_enroll_cancelled_current_behavior(auth_client, center, subject):
    klass = Class.objects.create(
        code="ADD-ENR-04",
        name="Cancelled current behavior",
        center=center,
        subject=subject,
        status="CANCELLED",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    student = User.objects.create_user(
        username="add_student_04",
        email="add_student_04@test.com",
        password="student123",
        role="STUDENT",
    )
    response = auth_client.post(
        reverse("enrollments:create"),
        {
            "student": student.pk,
            "klass": klass.pk,
            "status": EnrollmentStatus.NEW,
            "start_date": "2026-04-20",
            "fee_per_session": "300000",
            "sessions_purchased": "5",
            "amount_paid": "0",
            "note": "",
        },
    )
    assert response.status_code == 302
    assert Enrollment.objects.filter(klass=klass, student=student).exists()



