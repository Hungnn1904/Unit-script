"""
Test map for this file:

1.3 ClassSession.save (UT_CS_01..UT_CS_07)
- Kiem tra session_date validation, boundary dates, duplicate index, va null-date handling
- File nay dung de chay va chup ket qua phan 1.3 trong bao cao
"""

from datetime import date, time

import pytest
from django.db import IntegrityError
from django.urls import reverse

from apps.classes.models import Class, ClassSchedule
from apps.class_sessions.models import ClassSession


@pytest.mark.django_db
def test_ut_cs_01_session_date_valid(center, subject):
    """EP valid: session_date nằm trong [start, end]."""
    class_obj = Class.objects.create(
        code="CL-CS-01",
        name="Lop kiem tra session",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
    )

    session = ClassSession(
        klass=class_obj,
        index=1,
        date=date(2026, 4, 15),
    )
    session.save()

    assert ClassSession.objects.filter(klass=class_obj, date=date(2026, 4, 15)).exists(), (
        "Session row should exist in DB"
    )


@pytest.mark.django_db
def test_ut_cs_02_session_date_before_start(center, subject):
    """BVA: session_date < start_date -> expected ValidationError (not implemented yet)."""
    from django.core.exceptions import ValidationError

    class_obj = Class.objects.create(
        code="CL-CS-02",
        name="Lop kiem tra session",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
    )

    session = ClassSession(
        klass=class_obj,
        index=1,
        date=date(2026, 3, 31),
    )

    with pytest.raises(ValidationError, match="Session date must be within class period"):
        session.save()


@pytest.mark.django_db
def test_ut_cs_03_session_date_after_end(center, subject):
    """BVA: session_date > end_date -> expected ValidationError (not implemented yet)."""
    from django.core.exceptions import ValidationError

    class_obj = Class.objects.create(
        code="CL-CS-03",
        name="Lop kiem tra session",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
    )

    session = ClassSession(
        klass=class_obj,
        index=1,
        date=date(2026, 7, 1),
    )

    with pytest.raises(ValidationError, match="Session date must be within class period"):
        session.save()


@pytest.mark.django_db
def test_ut_cs_04_duplicate_session_index(center, subject):
    """Negative: duplicate session index for same class should violate unique constraint."""
    class_obj = Class.objects.create(
        code="CL-CS-04",
        name="Lop kiem tra session",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
    )

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

    session.save()

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

    session.save()

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

    session.save()

    assert ClassSession.objects.filter(klass=class_obj, date=date(2026, 5, 1)).exists()


@pytest.mark.django_db
def test_add_sec2_class_session_string_repr(center, subject):
    klass = Class.objects.create(
        code="ADD-CS-01",
        name="Lop kiem tra session",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
    )
    session = ClassSession.objects.create(klass=klass, index=1, date=date(2026, 4, 10))
    assert "Buổi 1" in str(session)


@pytest.mark.django_db
def test_add_sec2_class_schedule_timeslot(center, subject, auth_client):
    klass = Class.objects.create(code="ADD-CS-02", name="Timeslot", center=center, subject=subject, status="PLANNED")
    ClassSchedule.objects.create(
        klass=klass,
        day_of_week=ClassSchedule.DayOfWeek.MONDAY,
        start_time=time(8, 0),
        end_time=time(9, 30),
    )
    response = auth_client.get(reverse("classes:manage_classes"), {"group_by": "timeslot"})
    assert response.status_code == 200


@pytest.mark.django_db
def test_add_sec2_class_session_string_repr_index_two(center, subject):
    klass = Class.objects.create(
        code="ADD-CS-03",
        name="Lop kiem tra session",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
    )
    session = ClassSession.objects.create(klass=klass, index=2, date=date(2026, 4, 11))
    assert "Buổi 2" in str(session)


@pytest.mark.django_db
def test_add_sec2_class_schedule_timeslot_wednesday(center, subject, auth_client):
    klass = Class.objects.create(code="ADD-CS-04", name="Timeslot Wed", center=center, subject=subject, status="PLANNED")
    ClassSchedule.objects.create(
        klass=klass,
        day_of_week=ClassSchedule.DayOfWeek.WEDNESDAY,
        start_time=time(10, 0),
        end_time=time(11, 30),
    )
    response = auth_client.get(reverse("classes:manage_classes"), {"group_by": "timeslot"})
    assert response.status_code == 200
    assert ClassSchedule.objects.filter(klass=klass, day_of_week=ClassSchedule.DayOfWeek.WEDNESDAY).exists()


@pytest.mark.django_db
def test_add_sec2_same_date_different_index_allowed(center, subject):
    klass = Class.objects.create(
        code="ADD-CS-05",
        name="Same date allowed",
        center=center,
        subject=subject,
        status="PLANNED",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
    )
    ClassSession.objects.create(klass=klass, index=1, date=date(2026, 4, 12))
    ClassSession.objects.create(klass=klass, index=2, date=date(2026, 4, 12))
    assert ClassSession.objects.filter(klass=klass, date=date(2026, 4, 12)).count() == 2

