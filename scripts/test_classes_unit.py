"""
Test map for this file:

1) ClassCreateView (UT_CL_01..UT_CL_06)
    - Validate create-class behaviors via classes:class_add
    - Covers EP/BVA and invalid input handling

2) ClassSession.save (UT_CS_01..UT_CS_07)
    - Validate session persistence, boundary dates, duplicates, and null-date class handling

3) Class status state transitions (UT_ST_01..UT_ST_12)
    - Validate allowed/forbidden transitions through classes:class_edit
"""

import pytest
from datetime import date
from django.db import IntegrityError
from django.urls import reverse

from apps.classes.models import Class
from apps.class_sessions.models import ClassSession


def _build_class(center, subject, code="CL-TEST"):
    return Class.objects.create(
        code=code,
        name="Lop kiem tra session",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
    )


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


# -------------------------
# Section A: ClassCreateView
# UT_CL_01..UT_CL_06
# -------------------------


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
    assert "Ngày kết thúc phải >= ngày bắt đầu." in response.content.decode("utf-8", errors="ignore")
    assert Class.objects.count() == count_before, "No new class should be created when form is invalid"


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
def test_ut_cs_01_session_date_valid(center, subject):
    """EP valid: session_date nằm trong [start, end]."""
    class_obj = _build_class(center, subject, code="CL-CS-01")

    session = ClassSession(
        klass=class_obj,
        index=1,
        date=date(2026, 4, 15),
    )
    session.save()

    assert ClassSession.objects.filter(klass=class_obj, date=date(2026, 4, 15)).exists(), (
        "Session row should exist in DB"
    )


# -------------------------
# Section B: ClassSession.save
# UT_CS_01..UT_CS_07
# -------------------------


@pytest.mark.django_db
@pytest.mark.xfail(reason="ClassSession has no date-range validation in save/clean yet")
def test_ut_cs_02_session_date_before_start(center, subject):
    """BVA: session_date < start_date -> expected ValidationError (not implemented yet)."""
    from django.core.exceptions import ValidationError

    class_obj = _build_class(center, subject, code="CL-CS-02")

    session = ClassSession(
        klass=class_obj,
        index=1,
        date=date(2026, 3, 31),
    )

    with pytest.raises(ValidationError) as exc_info:
        session.save()

    assert "Session date must be within class period" in str(exc_info.value)


@pytest.mark.django_db
@pytest.mark.xfail(reason="ClassSession has no date-range validation in save/clean yet")
def test_ut_cs_03_session_date_after_end(center, subject):
    """BVA: session_date > end_date -> expected ValidationError (not implemented yet)."""
    from django.core.exceptions import ValidationError

    class_obj = _build_class(center, subject, code="CL-CS-03")

    session = ClassSession(
        klass=class_obj,
        index=1,
        date=date(2026, 7, 1),
    )

    with pytest.raises(ValidationError) as exc_info:
        session.save()

    assert "Session date must be within class period" in str(exc_info.value)


@pytest.mark.django_db
def test_ut_cs_04_duplicate_session_index(center, subject):
    """Negative: duplicate session index for same class should violate unique constraint."""
    class_obj = _build_class(center, subject, code="CL-CS-04")

    ClassSession.objects.create(
        klass=class_obj,
        index=1,
        date=date(2026, 4, 15),
    )

    with pytest.raises(IntegrityError):
        ClassSession.objects.create(
            klass=class_obj,
            index=1,
            date=date(2026, 5, 15),
        )


@pytest.mark.django_db
def test_ut_cs_05_session_date_at_start(center, subject):
    """UT_CS_05 - BVA: session_date == start_date."""
    class_obj = Class.objects.create(
        code="CL-SESS-05",
        name="Lop test bien bat dau",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
    )

    session = ClassSession(
        klass=class_obj,
        index=1,
        date=date(2026, 4, 1),
    )

    try:
        session.save()
    except Exception as e:
        pytest.fail(f"Unexpected exception at start_date boundary: {e}")

    assert ClassSession.objects.filter(klass=class_obj, date=date(2026, 4, 1)).exists()


@pytest.mark.django_db
def test_ut_cs_06_session_date_at_end(center, subject):
    """UT_CS_06 - BVA: session_date == end_date."""
    class_obj = Class.objects.create(
        code="CL-SESS-06",
        name="Lop test bien ket thuc",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
    )

    session = ClassSession(
        klass=class_obj,
        index=1,
        date=date(2026, 6, 30),
    )

    try:
        session.save()
    except Exception as e:
        pytest.fail(f"Unexpected exception at end_date boundary: {e}")

    assert ClassSession.objects.filter(klass=class_obj, date=date(2026, 6, 30)).exists()


@pytest.mark.django_db
def test_ut_cs_07_class_no_dates(center, subject):
    """UT_CS_07 - Null handling: class has no start/end dates."""
    class_obj = Class.objects.create(
        code="CL-SESS-07",
        name="Lop khong co ngay thang",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=None,
        end_date=None,
    )

    session = ClassSession(
        klass=class_obj,
        index=1,
        date=date(2026, 5, 1),
    )

    try:
        session.save()
    except TypeError as e:
        pytest.fail(f"Bug: TypeError when comparing date with None: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")

    assert ClassSession.objects.filter(klass=class_obj, date=date(2026, 5, 1)).exists()


def _status_update_response(auth_client, class_obj, center, subject, new_status):
    data = {
        "code": class_obj.code,
        "name": class_obj.name,
        "center": center.pk,
        "subject": subject.pk,
        "status": new_status,
        "schedules-TOTAL_FORMS": "0",
        "schedules-INITIAL_FORMS": "0",
        "schedules-MIN_NUM_FORMS": "0",
        "schedules-MAX_NUM_FORMS": "1000",
    }
    return auth_client.post(reverse("classes:class_edit", kwargs={"pk": class_obj.pk}), data)


# -------------------------
# Section C: State Transition
# UT_ST_01..UT_ST_12
# -------------------------


@pytest.mark.django_db
def test_ut_st_01_planned_to_ongoing(auth_client, center, subject):
    """UT_ST_01 (Valid): PLANNED -> ONGOING"""
    cls = Class.objects.create(code="ST-01", name="Test", center=center, subject=subject, status="PLANNED")
    response = _status_update_response(auth_client, cls, center, subject, "ONGOING")
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "ONGOING"


@pytest.mark.django_db
def test_ut_st_02_planned_to_completed(auth_client, center, subject):
    """UT_ST_02 (Invalid): PLANNED -> COMPLETED"""
    cls = Class.objects.create(code="ST-02", name="Test", center=center, subject=subject, status="PLANNED")
    _status_update_response(auth_client, cls, center, subject, "COMPLETED")
    cls.refresh_from_db()
    assert cls.status == "PLANNED", "Bug: allows skipping from PLANNED to COMPLETED"


@pytest.mark.django_db
def test_ut_st_03_planned_to_cancelled(auth_client, center, subject):
    """UT_ST_03 (Valid): PLANNED -> CANCELLED"""
    cls = Class.objects.create(code="ST-03", name="Test", center=center, subject=subject, status="PLANNED")
    response = _status_update_response(auth_client, cls, center, subject, "CANCELLED")
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "CANCELLED"


@pytest.mark.django_db
def test_ut_st_04_ongoing_to_planned(auth_client, center, subject):
    """UT_ST_04 (Invalid): ONGOING -> PLANNED"""
    cls = Class.objects.create(code="ST-04", name="Test", center=center, subject=subject, status="ONGOING")
    _status_update_response(auth_client, cls, center, subject, "PLANNED")
    cls.refresh_from_db()
    assert cls.status == "ONGOING", "Bug: allows rollback from ONGOING to PLANNED"


@pytest.mark.django_db
def test_ut_st_05_ongoing_to_completed(auth_client, center, subject):
    """UT_ST_05 (Valid): ONGOING -> COMPLETED"""
    cls = Class.objects.create(code="ST-05", name="Test", center=center, subject=subject, status="ONGOING")
    response = _status_update_response(auth_client, cls, center, subject, "COMPLETED")
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "COMPLETED"


@pytest.mark.django_db
def test_ut_st_06_ongoing_to_cancelled(auth_client, center, subject):
    """UT_ST_06 (Valid): ONGOING -> CANCELLED"""
    cls = Class.objects.create(code="ST-06", name="Test", center=center, subject=subject, status="ONGOING")
    response = _status_update_response(auth_client, cls, center, subject, "CANCELLED")
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "CANCELLED"


@pytest.mark.django_db
def test_ut_st_07_completed_to_planned(auth_client, center, subject):
    """UT_ST_07 (Invalid): COMPLETED -> PLANNED"""
    cls = Class.objects.create(code="ST-07", name="Test", center=center, subject=subject, status="COMPLETED")
    _status_update_response(auth_client, cls, center, subject, "PLANNED")
    cls.refresh_from_db()
    assert cls.status == "COMPLETED", "Bug: allows COMPLETED to PLANNED"


@pytest.mark.django_db
def test_ut_st_08_completed_to_ongoing(auth_client, center, subject):
    """UT_ST_08 (Invalid): COMPLETED -> ONGOING"""
    cls = Class.objects.create(code="ST-08", name="Test", center=center, subject=subject, status="COMPLETED")
    _status_update_response(auth_client, cls, center, subject, "ONGOING")
    cls.refresh_from_db()
    assert cls.status == "COMPLETED", "Bug: allows reopening COMPLETED class"


@pytest.mark.django_db
def test_ut_st_09_completed_to_cancelled(auth_client, center, subject):
    """UT_ST_09 (Invalid): COMPLETED -> CANCELLED"""
    cls = Class.objects.create(code="ST-09", name="Test", center=center, subject=subject, status="COMPLETED")
    _status_update_response(auth_client, cls, center, subject, "CANCELLED")
    cls.refresh_from_db()
    assert cls.status == "COMPLETED", "Bug: allows cancelling COMPLETED class"


@pytest.mark.django_db
def test_ut_st_10_cancelled_to_planned(auth_client, center, subject):
    """UT_ST_10 (Invalid): CANCELLED -> PLANNED"""
    cls = Class.objects.create(code="ST-10", name="Test", center=center, subject=subject, status="CANCELLED")
    _status_update_response(auth_client, cls, center, subject, "PLANNED")
    cls.refresh_from_db()
    assert cls.status == "CANCELLED", "Bug: allows reviving CANCELLED class to PLANNED"


@pytest.mark.django_db
def test_ut_st_11_cancelled_to_ongoing(auth_client, center, subject):
    """UT_ST_11 (Invalid): CANCELLED -> ONGOING"""
    cls = Class.objects.create(code="ST-11", name="Test", center=center, subject=subject, status="CANCELLED")
    _status_update_response(auth_client, cls, center, subject, "ONGOING")
    cls.refresh_from_db()
    assert cls.status == "CANCELLED", "Bug: allows reviving CANCELLED class to ONGOING"


@pytest.mark.django_db
def test_ut_st_12_cancelled_to_completed(auth_client, center, subject):
    """UT_ST_12 (Invalid): CANCELLED -> COMPLETED"""
    cls = Class.objects.create(code="ST-12", name="Test", center=center, subject=subject, status="CANCELLED")
    _status_update_response(auth_client, cls, center, subject, "COMPLETED")
    cls.refresh_from_db()
    assert cls.status == "CANCELLED", "Bug: allows CANCELLED class to COMPLETED"
