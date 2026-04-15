"""
Test map for this file:

Class status state transitions (UT_ST_01..UT_ST_12)
- Validate allowed/forbidden transitions through classes:class_edit
"""

import pytest
from django.urls import reverse

from apps.classes.models import Class


@pytest.mark.django_db
def test_ut_st_01_planned_to_ongoing(auth_client, center, subject):
    """UT_ST_01 (Valid): PLANNED -> ONGOING"""
    cls = Class.objects.create(code="ST-01", name="Test", center=center, subject=subject, status="PLANNED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "ONGOING",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "ONGOING"


@pytest.mark.django_db
def test_ut_st_02_planned_to_completed(auth_client, center, subject):
    """UT_ST_02 (Invalid): PLANNED -> COMPLETED"""
    cls = Class.objects.create(code="ST-02", name="Test", center=center, subject=subject, status="PLANNED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "COMPLETED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    invalid_response = response.status_code not in [204, 302]
    state_unchanged = cls.status == "PLANNED"
    assert all([invalid_response, state_unchanged]), "Bug: allows skipping from PLANNED to COMPLETED"


@pytest.mark.django_db
def test_ut_st_03_planned_to_cancelled(auth_client, center, subject):
    """UT_ST_03 (Valid): PLANNED -> CANCELLED"""
    cls = Class.objects.create(code="ST-03", name="Test", center=center, subject=subject, status="PLANNED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "CANCELLED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "CANCELLED"


@pytest.mark.django_db
def test_ut_st_04_ongoing_to_planned(auth_client, center, subject):
    """UT_ST_04 (Invalid): ONGOING -> PLANNED"""
    cls = Class.objects.create(code="ST-04", name="Test", center=center, subject=subject, status="ONGOING")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "PLANNED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    invalid_response = response.status_code not in [204, 302]
    state_unchanged = cls.status == "ONGOING"
    assert all([invalid_response, state_unchanged]), "Bug: allows rollback from ONGOING to PLANNED"


@pytest.mark.django_db
def test_ut_st_05_ongoing_to_completed(auth_client, center, subject):
    """UT_ST_05 (Valid): ONGOING -> COMPLETED"""
    cls = Class.objects.create(code="ST-05", name="Test", center=center, subject=subject, status="ONGOING")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "COMPLETED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "COMPLETED"


@pytest.mark.django_db
def test_ut_st_06_ongoing_to_cancelled(auth_client, center, subject):
    """UT_ST_06 (Valid): ONGOING -> CANCELLED"""
    cls = Class.objects.create(code="ST-06", name="Test", center=center, subject=subject, status="ONGOING")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "CANCELLED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "CANCELLED"


@pytest.mark.django_db
def test_ut_st_07_completed_to_planned(auth_client, center, subject):
    """UT_ST_07 (Invalid): COMPLETED -> PLANNED"""
    cls = Class.objects.create(code="ST-07", name="Test", center=center, subject=subject, status="COMPLETED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "PLANNED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    invalid_response = response.status_code not in [204, 302]
    state_unchanged = cls.status == "COMPLETED"
    assert all([invalid_response, state_unchanged]), "Bug: allows COMPLETED to PLANNED"


@pytest.mark.django_db
def test_ut_st_08_completed_to_ongoing(auth_client, center, subject):
    """UT_ST_08 (Invalid): COMPLETED -> ONGOING"""
    cls = Class.objects.create(code="ST-08", name="Test", center=center, subject=subject, status="COMPLETED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "ONGOING",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    invalid_response = response.status_code not in [204, 302]
    state_unchanged = cls.status == "COMPLETED"
    assert all([invalid_response, state_unchanged]), "Bug: allows reopening COMPLETED class"


@pytest.mark.django_db
def test_ut_st_09_completed_to_cancelled(auth_client, center, subject):
    """UT_ST_09 (Invalid): COMPLETED -> CANCELLED"""
    cls = Class.objects.create(code="ST-09", name="Test", center=center, subject=subject, status="COMPLETED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "CANCELLED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    invalid_response = response.status_code not in [204, 302]
    state_unchanged = cls.status == "COMPLETED"
    assert all([invalid_response, state_unchanged]), "Bug: allows cancelling COMPLETED class"


@pytest.mark.django_db
def test_ut_st_10_cancelled_to_planned(auth_client, center, subject):
    """UT_ST_10 (Invalid): CANCELLED -> PLANNED"""
    cls = Class.objects.create(code="ST-10", name="Test", center=center, subject=subject, status="CANCELLED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "PLANNED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    invalid_response = response.status_code not in [204, 302]
    state_unchanged = cls.status == "CANCELLED"
    assert all([invalid_response, state_unchanged]), "Bug: allows reviving CANCELLED class to PLANNED"


@pytest.mark.django_db
def test_ut_st_11_cancelled_to_ongoing(auth_client, center, subject):
    """UT_ST_11 (Invalid): CANCELLED -> ONGOING"""
    cls = Class.objects.create(code="ST-11", name="Test", center=center, subject=subject, status="CANCELLED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "ONGOING",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    invalid_response = response.status_code not in [204, 302]
    state_unchanged = cls.status == "CANCELLED"
    assert all([invalid_response, state_unchanged]), "Bug: allows reviving CANCELLED class to ONGOING"


@pytest.mark.django_db
def test_ut_st_12_cancelled_to_completed(auth_client, center, subject):
    """UT_ST_12 (Invalid): CANCELLED -> COMPLETED"""
    cls = Class.objects.create(code="ST-12", name="Test", center=center, subject=subject, status="CANCELLED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "COMPLETED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    invalid_response = response.status_code not in [204, 302]
    state_unchanged = cls.status == "CANCELLED"
    assert all([invalid_response, state_unchanged]), "Bug: allows CANCELLED class to COMPLETED"


@pytest.mark.django_db
def test_add_sec4_state_valid_planned_to_ongoing(auth_client, center, subject):
    cls = Class.objects.create(code="ADD-ST-01", name="State", center=center, subject=subject, status="PLANNED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "ONGOING",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "ONGOING"


@pytest.mark.django_db
def test_add_sec4_state_valid_ongoing_to_completed(auth_client, center, subject):
    cls = Class.objects.create(code="ADD-ST-02", name="State", center=center, subject=subject, status="ONGOING")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "COMPLETED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "COMPLETED"


@pytest.mark.django_db
def test_add_sec4_state_valid_planned_to_ongoing_alt(auth_client, center, subject):
    cls = Class.objects.create(code="ADD-ST-03", name="State Alt", center=center, subject=subject, status="PLANNED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "ONGOING",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "ONGOING"


@pytest.mark.django_db
def test_add_sec4_state_planned_to_completed_current_behavior(auth_client, center, subject):
    cls = Class.objects.create(code="ADD-ST-04", name="State current", center=center, subject=subject, status="PLANNED")
    response = auth_client.post(
        reverse("classes:class_edit", kwargs={"pk": cls.pk}),
        {
            "code": cls.code,
            "name": cls.name,
            "center": center.pk,
            "subject": subject.pk,
            "status": "COMPLETED",
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        },
    )
    cls.refresh_from_db()
    assert response.status_code in [204, 302]
    assert cls.status == "COMPLETED"

