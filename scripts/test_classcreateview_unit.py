"""
Test map for this file:

1.2 ClassCreateView (UT_CL_01..UT_CL_06)
- EP/BVA cho create class va duong dan invalid input
- File nay dung de chay va chup ket qua phan 1.2 trong bao cao
"""

import pytest
from django.urls import reverse

from apps.classes.models import Class


@pytest.mark.django_db
def test_ut_cl_01_end_equal_start(auth_client, center, subject):
    """
    UT_CL_01 - BVA: end_date == start_date
    Expected: Class is created successfully (status 204).
    """
    data = {
        "code": "CL-01",
        "name": "Lop 1 ngay",
        "center": center.pk,
        "subject": subject.pk,
        "status": "PLANNED",
        "start_date": "2026-04-10",
        "end_date": "2026-04-10",
        "schedules-TOTAL_FORMS": "0",
        "schedules-INITIAL_FORMS": "0",
        "schedules-MIN_NUM_FORMS": "0",
        "schedules-MAX_NUM_FORMS": "1000",
    }

    response = auth_client.post(reverse("classes:class_add"), data)

    assert response.status_code == 204, f"Expected 204, got {response.status_code}"

    klass = Class.objects.filter(code="CL-01").first()
    assert klass is not None, "Class row was not created"
    assert str(klass.start_date) == "2026-04-10"
    assert str(klass.end_date) == "2026-04-10"


@pytest.mark.django_db
def test_ut_cl_02_end_before_start(auth_client, center, subject):
    """
    UT_CL_02 - BVA: end_date = start_date - 1 day
    Expected: Form error (status 422), no new row in DB.
    """
    count_before = Class.objects.count()

    data = {
        "code": "CL-02",
        "name": "Lop loi ngay",
        "center": center.pk,
        "subject": subject.pk,
        "status": "PLANNED",
        "start_date": "2026-04-10",
        "end_date": "2026-04-09",
        "schedules-TOTAL_FORMS": "0",
        "schedules-INITIAL_FORMS": "0",
        "schedules-MIN_NUM_FORMS": "0",
        "schedules-MAX_NUM_FORMS": "1000",
    }

    response = auth_client.post(reverse("classes:class_add"), data)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    has_expected_message = "Ngày kết thúc phải >= ngày bắt đầu." in response.content.decode("utf-8", errors="ignore")
    count_unchanged = Class.objects.count() == count_before
    assert all([has_expected_message, count_unchanged]), (
        "Expected invalid-date message and unchanged class count"
    )


@pytest.mark.django_db
def test_ut_cl_03_missing_required_fields(auth_client, center, subject):
    """
    UT_CL_03 - EP invalid: Thiếu field bắt buộc (name, code)
    Expected: Form error (status 422), no new row in DB.
    """
    count_before = Class.objects.count()

    data = {
        "code": "",
        "name": "",
        "center": center.pk,
        "subject": subject.pk,
        "status": "PLANNED",
        "start_date": "2026-04-10",
        "end_date": "2026-04-20",
        "schedules-TOTAL_FORMS": "0",
        "schedules-INITIAL_FORMS": "0",
        "schedules-MIN_NUM_FORMS": "0",
        "schedules-MAX_NUM_FORMS": "1000",
    }

    response = auth_client.post(reverse("classes:class_add"), data)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    assert Class.objects.count() == count_before, "No new class should be created when required fields are missing"


@pytest.mark.django_db
def test_ut_cl_04_duplicate_code(auth_client, center, subject):
    """
    UT_CL_04 - Negative: Create 2 classes with same code (unique constraint)
    Expected: Second attempt rejected (status 422), DB only has 1 row.
    """
    Class.objects.create(
        code="CL-DUP",
        name="Lop goc",
        center=center,
        subject=subject,
        status="PLANNED",
    )

    count_before = Class.objects.count()

    data = {
        "code": "CL-DUP",
        "name": "Lop trung",
        "center": center.pk,
        "subject": subject.pk,
        "status": "PLANNED",
        "start_date": "2026-05-01",
        "end_date": "2026-05-31",
        "schedules-TOTAL_FORMS": "0",
        "schedules-INITIAL_FORMS": "0",
        "schedules-MIN_NUM_FORMS": "0",
        "schedules-MAX_NUM_FORMS": "1000",
    }

    response = auth_client.post(reverse("classes:class_add"), data)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    assert Class.objects.count() == count_before, "No new class should be created when code is duplicated"


@pytest.mark.django_db
def test_ut_cl_05_end_date_far_future(auth_client, center, subject):
    """
    UT_CL_05 - EP valid: start and end valid, end far in the future
    Expected: Class created successfully (status 204).
    """
    data = {
        "code": "CL-LONG",
        "name": "Lop dai han",
        "center": center.pk,
        "subject": subject.pk,
        "status": "PLANNED",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "schedules-TOTAL_FORMS": "0",
        "schedules-INITIAL_FORMS": "0",
        "schedules-MIN_NUM_FORMS": "0",
        "schedules-MAX_NUM_FORMS": "1000",
    }

    response = auth_client.post(reverse("classes:class_add"), data)

    assert response.status_code == 204, f"Expected 204, got {response.status_code}"

    klass = Class.objects.filter(code="CL-LONG").first()
    assert klass is not None, "Class was not created in DB"
    assert str(klass.start_date) == "2026-01-01"
    assert str(klass.end_date) == "2026-12-31"


@pytest.mark.django_db
def test_ut_cl_06_invalid_status_value(auth_client, center, subject):
    """
    UT_CL_06 - EP invalid: Gửi status không nằm trong danh sách choices
    (PLANNED / ONGOING / COMPLETED / CANCELLED)
    Expected: Form error (status 422), no new row in DB.
    """
    count_before = Class.objects.count()

    data = {
        "code": "CL-BAD-STATUS",
        "name": "Lop trang thai sai",
        "center": center.pk,
        "subject": subject.pk,
        "status": "INVALID_STATUS",
        "start_date": "2026-04-10",
        "end_date": "2026-04-20",
        "schedules-TOTAL_FORMS": "0",
        "schedules-INITIAL_FORMS": "0",
        "schedules-MIN_NUM_FORMS": "0",
        "schedules-MAX_NUM_FORMS": "1000",
    }

    response = auth_client.post(reverse("classes:class_add"), data)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    assert Class.objects.count() == count_before, "No new class should be created when status is invalid"
    assert not Class.objects.filter(code="CL-BAD-STATUS").exists(), (
        "DB should not have a class with invalid status"
    )


@pytest.mark.django_db
def test_add_sec1_class_create_get(auth_client):
    response = auth_client.get(reverse("classes:class_add"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_add_sec1_class_create_htmx_invalid(auth_client):
    response = auth_client.post(
        reverse("classes:class_add"),
        data={},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 422
    assert "HX-Trigger" in response


@pytest.mark.django_db
def test_add_sec1_class_create_get_contains_form_fields(auth_client):
    response = auth_client.get(reverse("classes:class_add"))
    assert response.status_code == 200
    assert response.context is not None
    assert "code" in response.context["form"].fields
    assert "end_date" in response.context["form"].fields


@pytest.mark.django_db
def test_add_sec1_class_create_invalid_date_keeps_count(auth_client, center, subject):
    count_before = Class.objects.count()
    response = auth_client.post(
        reverse("classes:class_add"),
        {
            "code": "CL-ADD-INV",
            "name": "Lop add invalid",
            "center": center.pk,
            "subject": subject.pk,
            "status": "PLANNED",
            "start_date": "2026-05-02",
            "end_date": "2026-05-01",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    assert response.status_code == 422
    assert Class.objects.count() == count_before

