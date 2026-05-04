"""
Merged Reports, Statistics & Session Management tests.
Tests: UT_RPT_01..UT_RPT_07 (Reports & Statistics)
Tests: UT_SES_01..UT_SES_05 (Session Management)
Features: Enrollment summary, Student report, Revenue report, Teaching hours, Class activity, Session detail/edit/photos
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import transaction
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import FileSystemStorage

from apps.class_sessions.models import ClassSessionPhoto
from apps.class_sessions import views as session_views


User = get_user_model()


@pytest.fixture(autouse=True)
def rollback_db(db):
    """Rollback every test transaction so data never leaks between cases."""
    with transaction.atomic():
        yield
        transaction.set_rollback(True)


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        password="admin123",
        email="admin@test.com",
    )


@pytest.fixture
def center(db):
    from apps.centers.models import Center

    return Center.objects.create(code="CTR-A", name="Center A")


@pytest.fixture
def other_center(db):
    from apps.centers.models import Center

    return Center.objects.create(code="CTR-B", name="Center B")


@pytest.fixture
def room(db, center):
    from apps.centers.models import Room

    return Room.objects.create(center=center, name="Room A")


@pytest.fixture
def subject(db):
    from apps.curriculum.models import Subject

    return Subject.objects.create(code="SUB-A", name="Python")


@pytest.fixture
def teacher_user(db, center):
    return User.objects.create_user(
        username="teacher1",
        password="teacher123",
        email="teacher1@test.com",
        role="TEACHER",
        center=center,
    )


@pytest.fixture
def assistant_user(db, center):
    return User.objects.create_user(
        username="assistant1",
        password="assistant123",
        email="assistant1@test.com",
        role="ASSISTANT",
        center=center,
    )


@pytest.fixture
def center_manager_user(db, center):
    return User.objects.create_user(
        username="manager1",
        password="manager123",
        email="manager1@test.com",
        role="CENTER_MANAGER",
        center=center,
    )


@pytest.fixture
def student_user(db, center):
    return User.objects.create_user(
        username="student1",
        password="student123",
        email="student1@test.com",
        role="STUDENT",
        center=center,
    )


@pytest.fixture
def other_student_user(db, other_center):
    return User.objects.create_user(
        username="student2",
        password="student223",
        email="student2@test.com",
        role="STUDENT",
        center=other_center,
    )


@pytest.fixture
def auth_client(client, admin_user):
    client.force_login(admin_user)
    return client


@pytest.fixture
def klass(db, center, subject, teacher_user, assistant_user):
    from apps.classes.models import Class, ClassAssistant

    klass = Class.objects.create(
        code="CLS-01",
        name="Class 01",
        center=center,
        subject=subject,
        main_teacher=teacher_user,
        status="ONGOING",
    )
    ClassAssistant.objects.create(klass=klass, assistant=assistant_user, scope="COURSE")
    return klass


@pytest.fixture
def other_klass(db, other_center, subject, teacher_user):
    from apps.classes.models import Class

    return Class.objects.create(
        code="CLS-02",
        name="Class 02",
        center=other_center,
        subject=subject,
        main_teacher=teacher_user,
        status="ONGOING",
    )


@pytest.fixture
def enrollment(db, klass, student_user):
    from apps.enrollments.models import Enrollment, EnrollmentStatus

    return Enrollment.objects.create(
        klass=klass,
        student=student_user,
        status=EnrollmentStatus.ACTIVE,
        fee_per_session=300000,
        sessions_purchased=12,
        amount_paid=3600000,
        sessions_consumed=0,
    )


@pytest.fixture
def other_enrollment(db, other_klass, other_student_user):
    from apps.enrollments.models import Enrollment, EnrollmentStatus

    return Enrollment.objects.create(
        klass=other_klass,
        student=other_student_user,
        status=EnrollmentStatus.ACTIVE,
        fee_per_session=300000,
        sessions_purchased=8,
        amount_paid=2400000,
        sessions_consumed=0,
    )


@pytest.fixture
def class_sessions(db, klass):
    from datetime import date, time

    from apps.class_sessions.models import ClassSession

    session1 = ClassSession.objects.create(
        klass=klass,
        index=1,
        date=date(2026, 4, 1),
        start_time=time(9, 0),
        end_time=time(10, 30),
        status="DONE",
    )
    session2 = ClassSession.objects.create(
        klass=klass,
        index=2,
        date=date(2026, 4, 8),
        start_time=time(9, 0),
        end_time=time(10, 30),
        status="MISSED",
    )
    session3 = ClassSession.objects.create(
        klass=klass,
        index=3,
        date=date(2026, 4, 15),
        start_time=time(9, 0),
        end_time=time(10, 30),
        status="PLANNED",
    )
    return session1, session2, session3


@pytest.fixture
def billing_entries(db, enrollment, other_enrollment):
    from datetime import datetime

    from apps.billing.models import BillingEntry

    purchase_1 = BillingEntry.objects.create(
        enrollment=enrollment,
        entry_type=BillingEntry.EntryType.PURCHASE,
        amount=1800000,
        sessions=6,
        unit_price=300000,
        discount_amount=0,
        created_at=datetime(2026, 4, 1, 10, 0, 0),
    )
    purchase_2 = BillingEntry.objects.create(
        enrollment=enrollment,
        entry_type=BillingEntry.EntryType.PURCHASE,
        amount=600000,
        sessions=2,
        unit_price=300000,
        discount_amount=0,
        created_at=datetime(2026, 4, 2, 10, 0, 0),
    )
    BillingEntry.objects.create(
        enrollment=other_enrollment,
        entry_type=BillingEntry.EntryType.PURCHASE,
        amount=2400000,
        sessions=8,
        unit_price=300000,
        discount_amount=0,
        created_at=datetime(2026, 4, 3, 10, 0, 0),
    )
    return purchase_1, purchase_2


@pytest.fixture
def attendance_records(db, class_sessions, student_user):
    from apps.attendance.models import Attendance

    session1, session2, _ = class_sessions
    Attendance.objects.create(session=session1, student=student_user, status="P")
    Attendance.objects.create(session=session2, student=student_user, status="A")


@pytest.fixture
def class_activity_records(db, class_sessions, student_user):
    from apps.attendance.models import Attendance
    from apps.students.models import StudentExerciseSubmission, StudentProduct
    from apps.curriculum.models import Exercise, Lesson, Module, Subject

    session1, session2, session3 = class_sessions
    Attendance.objects.create(session=session1, student=student_user, status="P")
    Attendance.objects.create(session=session2, student=student_user, status="A")
    Attendance.objects.create(session=session3, student=student_user, status="L")

    subject = Subject.objects.create(code="SUB-B", name="Web")
    module = Module.objects.create(subject=subject, order=1, title="Module 1")
    lesson = Lesson.objects.create(module=module, order=1, title="Lesson 1")
    exercise = Exercise.objects.create(lesson=lesson)
    StudentExerciseSubmission.objects.create(
        exercise=exercise,
        session=session1,
        student=student_user,
        title="Submission 1",
        description="Done",
    )
    StudentProduct.objects.create(
        session=session1,
        student=student_user,
        title="Product 1",
        description="Output",
    )
    StudentProduct.objects.create(
        session=session2,
        student=student_user,
        title="Product 2",
        description="Output 2",
    )


@pytest.fixture
def local_media_storage(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    if hasattr(settings, "STORAGES") and isinstance(settings.STORAGES, dict):
        settings.STORAGES["default"] = {"BACKEND": "django.core.files.storage.FileSystemStorage"}
    ClassSessionPhoto._meta.get_field("image").storage = FileSystemStorage(location=tmp_path)


@pytest.mark.django_db
def test_ut_rpt_01_enrollment_summary_role_based_access(auth_client, enrollment):
    """
    UT_RPT_01 - Enrollment summary accessible for admin.
    Expected: Admin gets 200 and sees summary data.
    """
    response = auth_client.get(reverse("reports:enrollment_summary"))

    assert response.status_code == 200
    assert "stats" in response.context
    assert response.context["stats"][0]["total"] == 1


@pytest.mark.django_db
def test_ut_rpt_02_enrollment_summary_center_manager_scope(client, center_manager_user, enrollment, other_enrollment):
    """
    UT_RPT_02 - Center manager should only see enrollments in own center.
    Expected: Only one enrollment counted for current center.
    """
    client.force_login(center_manager_user)
    response = client.get(reverse("reports:enrollment_summary"))

    assert response.status_code == 200
    assert response.context["stats"][0]["total"] == 1
    assert response.context["center"] == center_manager_user.center


@pytest.mark.django_db
def test_ut_rpt_03_student_report_aggregated_data_correctness(client, student_user, enrollment, attendance_records):
    """
    UT_RPT_03 - Student report should aggregate session counts correctly.
    Expected: total/completed/missed/attendance counts reflect created data.
    """
    client.force_login(student_user)
    response = client.get(reverse("reports:student_report"))

    assert response.status_code == 200
    rows = response.context["rows"]
    assert len(rows) == 1
    row = rows[0]
    assert row["total_sessions"] == 3
    assert row["completed_sessions"] == 2
    assert row["missed_sessions"] == 1
    assert row["attendance"]["P"] == 1
    assert row["attendance"]["A"] == 1
    assert row["progress_percent"] == 66


@pytest.mark.django_db
def test_ut_rpt_04_revenue_report_permission_gating(client, student_user):
    """
    UT_RPT_04 - Revenue report should deny access without permission.
    Expected: 403 for normal student.
    """
    client.force_login(student_user)
    response = client.get(reverse("reports:revenue_report"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_ut_rpt_05_revenue_report_allowed_with_permission(client, student_user, billing_entries):
    """
    UT_RPT_05 - Revenue report allowed when permission is granted.
    Expected: Totals and center aggregates are correct.
    """
    perm = Permission.objects.get(codename="view_revenue_report")
    student_user.user_permissions.add(perm)
    client.force_login(student_user)

    response = client.get(reverse("reports:revenue_report"))

    assert response.status_code == 200
    assert response.context["totals"]["total_amount"] == 4800000
    assert response.context["totals"]["total_sessions"] == 16
    assert len(list(response.context["by_center"])) == 2


@pytest.mark.django_db
def test_ut_rpt_06_teaching_hours_report_ep(client, teacher_user, class_sessions):
    """
    UT_RPT_06 - Teaching hours report aggregates teacher hours.
    Expected: One row for the main teacher with correct totals.
    """
    client.force_login(teacher_user)
    response = client.get(reverse("reports:teaching_hours_report"))

    assert response.status_code == 200
    rows = response.context["rows"]
    assert len(rows) == 1

    teacher_row = next(row for row in rows if row["user"].username == teacher_user.username)
    assert teacher_row["sessions_total"] == 3
    assert teacher_row["sessions_done"] == 1
    assert teacher_row["sessions_missed"] == 1
    assert teacher_row["sessions_cancelled"] == 0
    assert teacher_row["hours_total"] == 4.5
    assert teacher_row["hours_done"] == 1.5


@pytest.mark.django_db
def test_ut_rpt_07_class_activity_report_ep(client, teacher_user, class_activity_records):
    """
    UT_RPT_07 - Class activity report aggregates sessions, attendance and outputs.
    Expected: Correct session counts, attendance buckets, submissions, products.
    """
    perm = Permission.objects.get(codename="view_class_activity_report")
    teacher_user.user_permissions.add(perm)
    client.force_login(teacher_user)

    response = client.get(reverse("reports:class_activity_report"))

    assert response.status_code == 200
    rows = response.context["rows"]
    assert len(rows) == 1
    row = rows[0]
    assert row["total_sessions"] == 3
    assert row["done_sessions"] == 1
    assert row["missed_sessions"] == 1
    assert row["cancelled_sessions"] == 0
    assert row["attendance"]["P"] == 1
    assert row["attendance"]["A"] == 1
    assert row["attendance"]["L"] == 1
    assert row["submissions"] == 1
    assert row["products"] == 2
    assert row["products_per_session"] == 0.67


@pytest.mark.django_db
# UT_SES_01: Session detail view smoke test
def test_ut_ses_01_session_detail_view_smoke(auth_client, class_sessions):
    """UT_SES_01 - Session detail page should render basic information."""
    session, _, _ = class_sessions

    response = auth_client.get(reverse("class_sessions:session_detail", kwargs={"pk": session.pk}))

    assert response.status_code == 200
    assert response.context["session"].pk == session.pk
    assert "student_data_list" in response.context


@pytest.mark.django_db
# UT_SES_02: Override teacher per session without changing class default
def test_ut_ses_02_override_teacher_non_regression(auth_client, class_sessions, assistant_user):
    """UT_SES_02 - Override teacher on a session without changing class default teacher."""
    session, _, _ = class_sessions
    class_default_teacher_id = session.klass.main_teacher_id

    payload = {
        "klass": session.klass_id,
        "index": session.index,
        "date": session.date.isoformat() if session.date else "",
        "start_time": session.start_time.strftime("%H:%M") if session.start_time else "",
        "end_time": session.end_time.strftime("%H:%M") if session.end_time else "",
        "lesson": "",
        "status": session.status,
        "teacher_override": assistant_user.id,
        "room_override": "",
        "assistants": [],
    }

    response = auth_client.post(reverse("class_sessions:session_edit", kwargs={"pk": session.pk}), payload)

    assert response.status_code == 200
    session.refresh_from_db()
    session.klass.refresh_from_db()
    assert session.teacher_override_id == assistant_user.id
    assert session.klass.main_teacher_id == class_default_teacher_id


@pytest.mark.django_db
# UT_SES_03: Override room per session
def test_ut_ses_03_override_room_per_session(auth_client, class_sessions, room):
    """UT_SES_03 - Override room should be saved at session level."""
    session, _, _ = class_sessions

    payload = {
        "klass": session.klass_id,
        "index": session.index,
        "date": session.date.isoformat() if session.date else "",
        "start_time": session.start_time.strftime("%H:%M") if session.start_time else "",
        "end_time": session.end_time.strftime("%H:%M") if session.end_time else "",
        "lesson": "",
        "status": session.status,
        "teacher_override": "",
        "room_override": room.id,
        "assistants": [],
    }

    response = auth_client.post(reverse("class_sessions:session_edit", kwargs={"pk": session.pk}), payload)

    assert response.status_code == 200
    session.refresh_from_db()
    assert session.room_override_id == room.id


@pytest.mark.django_db
# UT_SES_04: Session status state transitions
def test_ut_ses_04_session_status_state_transition(auth_client, class_sessions):
    """UT_SES_04 - Session status transitions between valid states."""
    _, _, session = class_sessions

    for new_status in ["DONE", "MISSED", "CANCELLED"]:
        payload = {
            "klass": session.klass_id,
            "index": session.index,
            "date": session.date.isoformat() if session.date else "",
            "start_time": session.start_time.strftime("%H:%M") if session.start_time else "",
            "end_time": session.end_time.strftime("%H:%M") if session.end_time else "",
            "lesson": "",
            "status": new_status,
            "teacher_override": "",
            "room_override": "",
            "assistants": [],
        }

        response = auth_client.post(reverse("class_sessions:session_edit", kwargs={"pk": session.pk}), payload)
        assert response.status_code == 200
        session.refresh_from_db()
        assert session.status == new_status


@pytest.mark.django_db
# UT_SES_05: Session photos management (upload and delete)
def test_ut_ses_05_session_photos_management(auth_client, class_sessions, local_media_storage):
    """UT_SES_05 - Session photos should support upload and delete operations."""
    session, _, _ = class_sessions
    image = SimpleUploadedFile("session.jpg", b"fake-image-content", content_type="image/jpeg")

    upload_response = auth_client.post(
        reverse("class_sessions:session_photos_upload", kwargs={"pk": session.pk}),
        {"images": [image]},
    )

    assert upload_response.status_code in [302, 204]
    assert ClassSessionPhoto.objects.filter(session=session).count() == 1

    photo = ClassSessionPhoto.objects.filter(session=session).first()
    assert photo is not None

    delete_response = auth_client.post(
        reverse(
            "class_sessions:session_photo_delete",
            kwargs={"session_pk": session.pk, "photo_pk": photo.pk},
        )
    )

    assert delete_response.status_code in [302, 204]
    assert ClassSessionPhoto.objects.filter(session=session).count() == 0


@pytest.mark.django_db
# UT_SES_06: Session detail denied for non-staff without permission
def test_ut_ses_06_session_detail_forbidden_for_non_staff(client, class_sessions, student_user):
    session, _, _ = class_sessions
    client.force_login(student_user)

    response = client.get(reverse("class_sessions:session_detail", kwargs={"pk": session.pk}))

    assert response.status_code == 403


@pytest.mark.django_db
# UT_SES_07: Manage sessions denied without view permission
def test_ut_ses_07_manage_class_sessions_permission_denied(client, student_user):
    client.force_login(student_user)

    response = client.get(reverse("class_sessions:manage_class_sessions"))

    assert response.status_code == 403


@pytest.mark.django_db
# UT_SES_08: Manage sessions HTMX request handles invalid page gracefully
def test_ut_ses_08_manage_class_sessions_htmx_empty_page_falls_back(auth_client, class_sessions):
    response = auth_client.get(
        reverse("class_sessions:manage_class_sessions"),
        {"group_by": "date", "per_page": 2, "page": 99},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert response.context["page_obj"].number == 1
    assert response.context["per_page"] == 2
    assert response.context["group_by"] == "date"


@pytest.mark.django_db
# UT_SES_09: Session photos upload rejects non-POST methods
def test_ut_ses_09_session_photos_upload_rejects_get(auth_client, class_sessions):
    session, _, _ = class_sessions

    response = auth_client.get(reverse("class_sessions:session_photos_upload", kwargs={"pk": session.pk}))

    assert response.status_code == 400


@pytest.mark.django_db
# UT_SES_10: Session photos upload rejects empty payload
def test_ut_ses_10_session_photos_upload_requires_files(auth_client, class_sessions):
    session, _, _ = class_sessions

    response = auth_client.post(reverse("class_sessions:session_photos_upload", kwargs={"pk": session.pk}), {})

    assert response.status_code == 400


@pytest.mark.django_db
# UT_SES_11: Session photos upload HTMX returns redirect header
def test_ut_ses_11_session_photos_upload_htmx_headers(auth_client, class_sessions, local_media_storage):
    session, _, _ = class_sessions
    image = SimpleUploadedFile("session-extra.jpg", b"fake-image-content", content_type="image/jpeg")

    before_count = ClassSessionPhoto.objects.filter(session=session).count()
    response = auth_client.post(
        reverse("class_sessions:session_photos_upload", kwargs={"pk": session.pk}) + "?as_page=true",
        {"images": [image]},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 204
    assert "HX-Redirect" in response
    assert reverse("class_sessions:session_detail", args=[session.pk]) in response["HX-Redirect"]
    assert "HX-Trigger" in response
    assert ClassSessionPhoto.objects.filter(session=session).count() == before_count + 1


@pytest.mark.django_db
# UT_SES_12: Session photo delete requires POST
def test_ut_ses_12_session_photo_delete_requires_post(auth_client, class_sessions, local_media_storage):
    session, _, _ = class_sessions
    image = SimpleUploadedFile("for-get-check.jpg", b"fake-image-content", content_type="image/jpeg")
    photo = ClassSessionPhoto.objects.create(
        session=session,
        image=image,
        uploaded_by=session.klass.main_teacher,
    )

    response = auth_client.get(
        reverse(
            "class_sessions:session_photo_delete",
            kwargs={"session_pk": session.pk, "photo_pk": photo.pk},
        )
    )

    assert response.status_code == 405


@pytest.mark.django_db
# UT_SES_13: Session photo delete HTMX path returns 204 and trigger
def test_ut_ses_13_session_photo_delete_htmx_success(auth_client, class_sessions, local_media_storage):
    session, _, _ = class_sessions
    image = SimpleUploadedFile("for-htmx-delete.jpg", b"fake-image-content", content_type="image/jpeg")
    photo = ClassSessionPhoto.objects.create(
        session=session,
        image=image,
        uploaded_by=session.klass.main_teacher,
    )

    response = auth_client.post(
        reverse(
            "class_sessions:session_photo_delete",
            kwargs={"session_pk": session.pk, "photo_pk": photo.pk},
        ) + "?as_page=true",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 204
    assert "HX-Trigger" in response
    assert not ClassSessionPhoto.objects.filter(pk=photo.pk).exists()


@pytest.mark.django_db
# UT_SES_14: parse date helper supports multiple input formats and fallback
def test_ut_ses_14_parse_date_param_formats_and_fallback():
    from datetime import date

    default_day = date(2026, 1, 1)

    assert session_views._parse_date_param("2026-04-20", default_day) == date(2026, 4, 20)
    assert session_views._parse_date_param("20/04/2026", default_day) == date(2026, 4, 20)
    assert session_views._parse_date_param("invalid", default_day) == default_day
    assert session_views._parse_date_param("", default_day) == default_day


@pytest.mark.django_db
# UT_SES_15: session group label helper covers all grouping branches
def test_ut_ses_15_session_group_label_branches(class_sessions):
    session, _, _ = class_sessions

    assert session_views._session_group_label(session, "subject") == session.klass.subject.name
    assert session_views._session_group_label(session, "center") == session.klass.center.name
    assert session_views._session_group_label(session, "teacher") == session.klass.main_teacher.display_name_with_email
    assert session_views._session_group_label(session, "status") == session.get_status_display()
    assert session_views._session_group_label(session, "timeslot") == "09:00 - 10:30"
    assert session_views._session_group_label(session, "date") == "01/04/2026"
    assert session_views._session_group_label(session, "unknown") == ""


@pytest.mark.django_db
# UT_SES_16: user display helper falls back from display name to full name to username
def test_ut_ses_16_user_display_name_fallbacks(db, center):
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="display_user",
        password="pass123",
        email="display@test.com",
        first_name="Display",
        last_name="Name",
        role="TEACHER",
        center=center,
    )

    assert session_views._user_display_name(None) == ""
    assert session_views._user_display_name(user) == user.display_name_with_email


@pytest.mark.django_db
# UT_SES_17: session staff helper recognizes main teacher and assistant
def test_ut_ses_17_user_is_session_staff_paths(class_sessions, teacher_user, assistant_user, student_user):
    session, _, _ = class_sessions

    assert session_views._user_is_session_staff(session, teacher_user) is True
    assert session_views._user_is_session_staff(session, assistant_user) is True
    assert session_views._user_is_session_staff(session, student_user) is False
