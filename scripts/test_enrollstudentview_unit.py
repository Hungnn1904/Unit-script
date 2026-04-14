"""
Test map for this file:

EnrollStudentView / Enrollment create (UT_ENR_01..UT_ENR_06)
- Covers Decision Table scenarios by class status
- Covers duplicate enrollment and invalid id negative paths
"""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.classes.models import Class
from apps.enrollments.models import Enrollment, EnrollmentStatus


User = get_user_model()


def _create_student_user(username: str, email: str) -> User:
    return User.objects.create_user(
        username=username,
        email=email,
        password="student123",
        role="STUDENT",
    )


def _enrollment_post_data(klass, student, status=EnrollmentStatus.NEW):
    return {
        "student": student.pk,
        "klass": klass.pk,
        "status": status,
        "start_date": "2026-04-10",
        "fee_per_session": "300000",
        "sessions_purchased": "10",
        "amount_paid": "0",
        "note": "",
    }


def _create_class(code: str, name: str, center, subject, status: str):
    return Class.objects.create(
        code=code,
        name=name,
        center=center,
        subject=subject,
        status=status,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )


# -------------------------
# Section D: EnrollStudentView
# UT_ENR_01..UT_ENR_06
# -------------------------


@pytest.mark.django_db
def test_ut_enr_01_enroll_ongoing_class(auth_client, center, subject):
    """
    UT_ENR_01 - Decision Table: Class Ongoing x New Student -> Allow
    """
    class_obj = _create_class("CL-ENR-01", "Lop Dang Dien Ra", center, subject, "ONGOING")
    student = _create_student_user("student_a", "a@test.com")

    response = auth_client.post(
        reverse("enrollments:create"),
        _enrollment_post_data(class_obj, student),
    )

    assert response.status_code == 302, f"Expected 302, got {response.status_code}"
    assert Enrollment.objects.filter(klass=class_obj, student=student).exists(), "Enrollment row should be created"


@pytest.mark.django_db
def test_ut_enr_02_enroll_cancelled_class(auth_client, center, subject):
    """
    UT_ENR_02 - Decision Table: Class Cancelled x Any -> Deny
    """
    class_obj = _create_class("CL-ENR-02", "Lop Da Huy", center, subject, "CANCELLED")
    student = _create_student_user("student_b", "b@test.com")
    count_before = Enrollment.objects.count()

    response = auth_client.post(
        reverse("enrollments:create"),
        _enrollment_post_data(class_obj, student),
    )

    assert response.status_code != 302, "Cancelled class should not allow successful enrollment"
    assert Enrollment.objects.count() == count_before, "No new enrollment should be created"


@pytest.mark.django_db
def test_ut_enr_03_duplicate_enrollment(auth_client, center, subject):
    """
    UT_ENR_03 - Negative: Duplicate enrollment -> Reject
    """
    class_obj = _create_class("CL-ENR-03", "Lop Test Duplicate", center, subject, "ONGOING")
    student = _create_student_user("student_c", "c@test.com")

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
        _enrollment_post_data(class_obj, student),
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
    class_obj = _create_class("CL-ENR-04", "Lop Sap Khai Giang", center, subject, "PLANNED")
    student = _create_student_user("student_d", "d@test.com")

    response = auth_client.post(
        reverse("enrollments:create"),
        _enrollment_post_data(class_obj, student),
    )

    assert response.status_code == 302, f"Expected 302, got {response.status_code}"
    assert Enrollment.objects.filter(klass=class_obj, student=student).exists()


@pytest.mark.django_db
def test_ut_enr_05_enroll_completed_class(auth_client, center, subject):
    """
    UT_ENR_05 - Decision Table: Class Completed x New Student -> Deny
    """
    class_obj = _create_class("CL-ENR-05", "Lop Da Ket Thuc", center, subject, "COMPLETED")
    student = _create_student_user("student_e", "e@test.com")
    count_before = Enrollment.objects.count()

    response = auth_client.post(
        reverse("enrollments:create"),
        _enrollment_post_data(class_obj, student),
    )

    assert response.status_code != 302, "Completed class should not allow successful enrollment"
    assert Enrollment.objects.count() == count_before, "No new enrollment should be created"


@pytest.mark.django_db
def test_ut_enr_06_enroll_invalid_ids(auth_client, center, subject):
    """
    UT_ENR_06 - Negative Testing: non-existent student id
    """
    class_obj = _create_class("CL-ENR-06", "Lop Test Loi ID", center, subject, "PLANNED")
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
