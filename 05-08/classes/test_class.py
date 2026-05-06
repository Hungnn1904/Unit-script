"""
Pytest test suite for apps/classes
Covers: Models, Forms, Views (permissions + business logic)

Requirements:
    pip install pytest pytest-django factory-boy

pytest.ini (hoặc pyproject.toml):
    [pytest]
    DJANGO_SETTINGS_MODULE = your_project.settings
    python_files = test_*.py
"""

import json
import pytest
from datetime import date, time, timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def client():
    return Client()


@pytest.fixture
def center(db):
    from apps.centers.models import Center
    return Center.objects.create(name="Trung tâm A")


@pytest.fixture
def subject(db):
    from apps.curriculum.models import Subject
    return Subject.objects.create(name="Toán", code="MATH")


@pytest.fixture
def teacher(db):
    return User.objects.create_user(
        username="teacher01",
        password="pass1234",
        role="TEACHER",
        first_name="Nguyễn",
        last_name="Văn A",
    )


@pytest.fixture
def assistant_user(db):
    return User.objects.create_user(
        username="assistant01",
        password="pass1234",
        role="ASSISTANT",
    )


@pytest.fixture
def staff_user(db):
    """User có đầy đủ permission classes.*"""
    user = User.objects.create_user(username="staff01", password="pass1234")
    for codename in ["view_class", "add_class", "change_class", "delete_class"]:
        ct = ContentType.objects.get(app_label="classes", model="class")
        perm = Permission.objects.get(content_type=ct, codename=codename)
        user.user_permissions.add(perm)
    # permission class_sessions.change_classsession
    try:
        ct2 = ContentType.objects.get(app_label="class_sessions", model="classsession")
        perm2 = Permission.objects.get(content_type=ct2, codename="change_classsession")
        user.user_permissions.add(perm2)
    except Exception:
        pass
    return user


@pytest.fixture
def no_perm_user(db):
    return User.objects.create_user(username="noperm", password="pass1234")


@pytest.fixture
def klass(db, center, subject, teacher):
    from apps.classes.models import Class
    return Class.objects.create(
        code="LOP001",
        name="Lớp Toán 10A",
        center=center,
        subject=subject,
        main_teacher=teacher,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        status="PLANNED",
    )


@pytest.fixture
def klass_with_schedule(db, klass):
    from apps.classes.models import ClassSchedule
    ClassSchedule.objects.create(
        klass=klass,
        day_of_week=date.today().weekday(),  # hôm nay
        start_time=time(8, 0),
        end_time=time(9, 30),
    )
    return klass


@pytest.fixture
def lessons(db, subject):
    """Tạo 3 bài học cho môn subject"""
    from apps.curriculum.models import Module, Lesson
    module = Module.objects.create(subject=subject, title="Chương 1", order=1)
    lessons = []
    for i in range(1, 4):
        lessons.append(
            Lesson.objects.create(module=module, title=f"Bài {i}", order=i)
        )
    return lessons


# ==============================================================================
# 1. MODELS — Ràng buộc dữ liệu
# ==============================================================================

@pytest.mark.django_db
class TestClassModel:

    def test_create_class_success(self, center, subject, teacher):
        from apps.classes.models import Class
        """TC-13 (variant): Tạo Class hợp lệ lưu vào DB"""
        from apps.classes.models import Class
        klass = Class.objects.create(
            code="LOP999",
            name="Lớp Test",
            center=center,
            subject=subject,
            main_teacher=teacher,
            status="PLANNED",
        )
        assert klass.pk is not None
        assert str(klass) == "LOP999 - Lớp Test"

    def test_class_code_unique(self, klass, center, subject):
        """TC-13: code phải unique → IntegrityError"""
        from apps.classes.models import Class
        with pytest.raises(IntegrityError):
            Class.objects.create(
                code=klass.code,  # trùng
                name="Lớp khác",
                center=center,
                subject=subject,
            )

    def test_class_center_protect_on_delete(self, klass):
        """TC-16: Xóa Center khi còn Class → PROTECT"""
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            klass.center.delete()

    def test_class_subject_protect_on_delete(self, klass):
        """TC-16: Xóa Subject khi còn Class → PROTECT"""
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            klass.subject.delete()

    def test_update_class_details(self, klass):
        """TC03: Cập nhật thông tin lớp học."""
        from apps.classes.models import Class # Import Class here
        klass.name = "Lớp Toán Nâng Cao"
        klass.status = "ONGOING"
        klass.save()
        updated_klass = Class.objects.get(pk=klass.pk)
        assert updated_klass.name == "Lớp Toán Nâng Cao"
        assert updated_klass.status == "ONGOING"

    def test_filter_classes_by_status(self, center, subject, teacher):
        """TC05: Lọc danh sách lớp học theo trạng thái (đang mở, đã đóng)."""
        from apps.classes.models import Class # Import Class here
        Class.objects.create(code="C002", name="Lớp Kế hoạch", center=center, subject=subject, status="PLANNED")
        Class.objects.create(code="C003", name="Lớp Đang diễn ra", center=center, subject=subject, status="ONGOING")
        Class.objects.create(code="C004", name="Lớp Đã hoàn thành", center=center, subject=subject, status="COMPLETED")

        planned_classes = Class.objects.filter(status="PLANNED")
        ongoing_classes = Class.objects.filter(status="ONGOING")
        completed_classes = Class.objects.filter(status="COMPLETED")

        assert planned_classes.count() == 1
        assert planned_classes.first().code == "C002"
        assert ongoing_classes.count() == 1
        assert ongoing_classes.first().code == "C003"
        assert completed_classes.count() == 1
        assert completed_classes.first().code == "C004"


@pytest.mark.django_db
class TestClassScheduleModel:

    def test_create_schedule_success(self, klass):
        """Tạo ClassSchedule hợp lệ"""
        from apps.classes.models import ClassSchedule
        s = ClassSchedule.objects.create(
            klass=klass,
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(9, 30),
        )
        assert s.pk is not None

    def test_schedule_unique_together(self, klass):
        """TC-14: unique (klass, day_of_week, start_time) → IntegrityError"""
        from apps.classes.models import ClassSchedule
        ClassSchedule.objects.create(
            klass=klass, day_of_week=1, start_time=time(8, 0), end_time=time(9, 30)
        )
        with pytest.raises(IntegrityError):
            ClassSchedule.objects.create(
                klass=klass, day_of_week=1, start_time=time(8, 0), end_time=time(10, 0)
            )


@pytest.mark.django_db
class TestClassAssistantModel:

    def test_class_assistant_unique_together(self, klass, assistant_user):
        """TC-15: unique (klass, assistant, scope) → IntegrityError"""
        from apps.classes.models import ClassAssistant
        ClassAssistant.objects.create(klass=klass, assistant=assistant_user, scope="COURSE")
        with pytest.raises(IntegrityError):
            ClassAssistant.objects.create(klass=klass, assistant=assistant_user, scope="COURSE")

    def test_class_assistant_different_scope_allowed(self, klass, assistant_user):
        """Cùng klass + assistant nhưng scope khác → OK"""
        from apps.classes.models import ClassAssistant
        ClassAssistant.objects.create(klass=klass, assistant=assistant_user, scope="COURSE")
        ca = ClassAssistant.objects.create(klass=klass, assistant=assistant_user, scope="SESSION")
        assert ca.pk is not None


# ==============================================================================
# 2. FORMS — Validation nghiệp vụ
# ==============================================================================

@pytest.mark.django_db
class TestClassForm:

    def _base_data(self, center, subject):
        return {
            "code": "FORM001",
            "name": "Lớp Form Test",
            "center": center.pk,
            "subject": subject.pk,
            "status": "PLANNED",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=10)).isoformat(),
        }

    def test_form_valid(self, center, subject):
        """TC-19 (variant): Form hợp lệ"""
        from apps.classes.forms import ClassForm
        data = self._base_data(center, subject)
        form = ClassForm(data=data)
        assert form.is_valid(), form.errors

    def test_end_date_before_start_date(self, center, subject):
        """TC-17: end_date < start_date → lỗi end_date"""
        from apps.classes.forms import ClassForm
        data = self._base_data(center, subject)
        data["start_date"] = date.today().isoformat()
        data["end_date"] = (date.today() - timedelta(days=1)).isoformat()
        form = ClassForm(data=data)
        assert not form.is_valid()
        assert "end_date" in form.errors

    def test_main_teacher_in_assistants_raises(self, center, subject, teacher):
        """TC-18: main_teacher trùng assistants → ValidationError"""
        from apps.classes.forms import ClassForm
        data = self._base_data(center, subject)
        data["main_teacher"] = teacher.pk
        data["assistants"] = [teacher.pk]
        form = ClassForm(data=data)
        assert not form.is_valid()
        assert any("trợ giảng" in str(e).lower() or "không được" in str(e).lower()
                   for e in form.errors.get("assistants", []))

    def test_create_class_with_schedule_via_formset(self, center, subject, teacher):
        """TC-19: POST hợp lệ tạo class + lịch học → đủ quan hệ DB"""
        from apps.classes.forms import ClassForm, ClassScheduleFormSet
        data = self._base_data(center, subject)
        data["main_teacher"] = teacher.pk

        formset_data = {
            "schedules-TOTAL_FORMS": "1",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
            "schedules-0-day_of_week": "0",
            "schedules-0-start_time": "08:00",
            "schedules-0-end_time": "09:30",
            "schedules-0-DELETE": "",
        }
        form = ClassForm(data=data)
        formset = ClassScheduleFormSet(data=formset_data, prefix="schedules")
        assert form.is_valid(), form.errors
        assert formset.is_valid(), formset.errors

        klass = form.save()
        formset.instance = klass
        formset.save()

        assert klass.weekly_schedules.count() == 1
        schedule = klass.weekly_schedules.first()
        assert schedule.day_of_week == 0
        assert schedule.start_time == time(8, 0)


# ==============================================================================
# 3. VIEWS — Phân quyền (Security)
# ==============================================================================

@pytest.mark.django_db
class TestManageClassesPermissions:

    def test_anonymous_redirect_login(self, client):
        """TC-20: Anonymous → redirect login"""
        url = reverse("classes:manage_classes")
        resp = client.get(url)
        assert resp.status_code == 302
        assert "/login" in resp["Location"] or "/accounts/login" in resp["Location"]

    def test_no_perm_raises_403(self, client, no_perm_user):
        """TC-21: Không có perm view_class → 403"""
        client.force_login(no_perm_user)
        url = reverse("classes:manage_classes")
        resp = client.get(url)
        assert resp.status_code == 403

    def test_with_perm_returns_200(self, client, staff_user):
        """TC-21 (pass): Có perm → 200"""
        client.force_login(staff_user)
        url = reverse("classes:manage_classes")
        resp = client.get(url)
        assert resp.status_code == 200

    def test_htmx_returns_partial(self, client, staff_user):
        """HTMX request → render partial template"""
        client.force_login(staff_user)
        url = reverse("classes:manage_classes")
        resp = client.get(url, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        # Partial không chứa layout đầy đủ
        assert b"manage_classes" not in resp.content or b"filterable-content" in resp.content


@pytest.mark.django_db
class TestClassDetailPermissions:

    def test_main_teacher_can_view_own_class(self, client, klass, teacher):
        """TC-22: Main teacher xem lớp mình → 200 (bypass perm)"""
        client.force_login(teacher)
        url = reverse("classes:class_detail", kwargs={"pk": klass.pk})
        resp = client.get(url)
        assert resp.status_code == 200

    def test_assistant_can_view_class(self, client, klass, assistant_user):
        """TC-22: Assistant xem lớp hỗ trợ → 200"""
        klass.assistants.add(assistant_user)
        client.force_login(assistant_user)
        url = reverse("classes:class_detail", kwargs={"pk": klass.pk})
        resp = client.get(url)
        assert resp.status_code == 200

    def test_unrelated_user_gets_403(self, client, klass, no_perm_user):
        """TC-23: User không liên quan → 403"""
        client.force_login(no_perm_user)
        url = reverse("classes:class_detail", kwargs={"pk": klass.pk})
        resp = client.get(url)
        assert resp.status_code == 403


# ==============================================================================
# 4. VIEWS — Business Logic: class_delete_view
# ==============================================================================

@pytest.mark.django_db
class TestClassDeleteView:

    def test_delete_with_sessions_returns_400(self, client, staff_user, klass_with_schedule):
        """TC-9: Còn sessions → từ chối xóa (400)"""
        from apps.class_sessions.models import ClassSession
        # Tạo 1 session cho lớp
        ClassSession.objects.create(
            klass=klass_with_schedule,
            date=date.today(),
            start_time=time(8, 0),
            end_time=time(9, 30),
            status="PLANNED",
            index=1,
        )
        client.force_login(staff_user)
        url = reverse("classes:class_delete", kwargs={"pk": klass_with_schedule.pk})
        resp = client.post(url)
        assert resp.status_code == 400
        trigger = json.loads(resp["HX-Trigger"])
        assert trigger["show-sweet-alert"]["icon"] == "error"

    def test_delete_without_sessions_succeeds(self, client, staff_user, klass):
        """TC-10: Không có sessions → xóa thành công"""
        from apps.classes.models import Class
        pk = klass.pk
        client.force_login(staff_user)
        url = reverse("classes:class_delete", kwargs={"pk": pk})
        resp = client.post(url)
        assert resp.status_code == 200
        assert not Class.objects.filter(pk=pk).exists()
        trigger = json.loads(resp["HX-Trigger"])
        assert trigger["show-sweet-alert"]["icon"] == "success"

    def test_delete_get_method_not_allowed(self, client, staff_user, klass):
        """require_POST: GET → 405"""
        client.force_login(staff_user)
        url = reverse("classes:class_delete", kwargs={"pk": klass.pk})
        resp = client.get(url)
        assert resp.status_code == 405


# ==============================================================================
# 5. VIEWS — Business Logic: class_edit_view
# ==============================================================================

@pytest.mark.django_db
class TestClassEditView:

    def _post_data(self, klass):
        """Data POST hợp lệ để update class"""
        return {
            "code": klass.code,
            "name": klass.name,
            "center": klass.center.pk,
            "subject": klass.subject.pk,
            "status": klass.status,
            "start_date": klass.start_date.isoformat(),
            "end_date": klass.end_date.isoformat(),
            "schedules-TOTAL_FORMS": "0",
            "schedules-INITIAL_FORMS": "0",
            "schedules-MIN_NUM_FORMS": "0",
            "schedules-MAX_NUM_FORMS": "1000",
        }

    def test_schedule_changed_deletes_planned_sessions(self, client, staff_user, klass_with_schedule):
        """TC-11: Lịch thay đổi → xóa PLANNED sessions"""
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import ClassSchedule

        # Tạo 1 PLANNED session
        ClassSession.objects.create(
            klass=klass_with_schedule,
            date=date.today() + timedelta(days=7),
            start_time=time(8, 0),
            end_time=time(9, 30),
            status="PLANNED",
            index=1,
        )
        assert ClassSession.objects.filter(klass=klass_with_schedule, status="PLANNED").count() == 1

        # Gửi POST với lịch mới (thêm 1 lịch khác ngày)
        data = self._post_data(klass_with_schedule)
        existing_schedule = klass_with_schedule.weekly_schedules.first()
        data.update({
            "schedules-TOTAL_FORMS": "1",
            "schedules-INITIAL_FORMS": "1",
            f"schedules-0-id": existing_schedule.pk,
            f"schedules-0-day_of_week": (existing_schedule.day_of_week + 1) % 7,  # đổi ngày
            f"schedules-0-start_time": "10:00",
            f"schedules-0-end_time": "11:30",
        })

        client.force_login(staff_user)
        url = reverse("classes:class_edit", kwargs={"pk": klass_with_schedule.pk})
        resp = client.post(url, data=data)
        assert resp.status_code == 204
        # PLANNED sessions phải bị xóa
        assert ClassSession.objects.filter(klass=klass_with_schedule, status="PLANNED").count() == 0

    def test_schedule_unchanged_keeps_sessions(self, client, staff_user, klass_with_schedule):
        """TC-12: Lịch không đổi → giữ nguyên sessions"""
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import ClassSchedule

        session = ClassSession.objects.create(
            klass=klass_with_schedule,
            date=date.today() + timedelta(days=7),
            start_time=time(8, 0),
            end_time=time(9, 30),
            status="PLANNED",
            index=1,
        )

        # Gửi POST với đúng lịch cũ (không thay đổi)
        data = self._post_data(klass_with_schedule)
        existing_schedule = klass_with_schedule.weekly_schedules.first()
        data.update({
            "schedules-TOTAL_FORMS": "1",
            "schedules-INITIAL_FORMS": "1",
            f"schedules-0-id": existing_schedule.pk,
            f"schedules-0-day_of_week": existing_schedule.day_of_week,
            f"schedules-0-start_time": existing_schedule.start_time.strftime("%H:%M"),
            f"schedules-0-end_time": existing_schedule.end_time.strftime("%H:%M"),
        })

        client.force_login(staff_user)
        url = reverse("classes:class_edit", kwargs={"pk": klass_with_schedule.pk})
        resp = client.post(url, data=data)
        assert resp.status_code == 204
        # Session vẫn còn
        assert ClassSession.objects.filter(pk=session.pk).exists()


# ==============================================================================
# 6. VIEWS — Business Logic: generate_sessions
# ==============================================================================

@pytest.mark.django_db
class TestGenerateSessions:

    def _post(self, client, staff_user, klass):
        client.force_login(staff_user)
        url = reverse("classes:generate_sessions", kwargs={"pk": klass.pk})
        return client.post(url)

    def test_no_start_end_date_returns_400(self, client, staff_user, center, subject):
        """TC-6: Thiếu start_date/end_date → 400"""
        from apps.classes.models import Class
        klass = Class.objects.create(
            code="NOGEN01", name="No Date", center=center, subject=subject
        )
        resp = self._post(client, staff_user, klass)
        assert resp.status_code == 400
        trigger = json.loads(resp["HX-Trigger"])
        assert trigger["show-sweet-alert"]["icon"] == "error"

    def test_no_schedule_returns_400(self, client, staff_user, klass):
        """TC-7: Thiếu lịch tuần → 400"""
        resp = self._post(client, staff_user, klass)
        assert resp.status_code == 400
        trigger = json.loads(resp["HX-Trigger"])
        assert "lịch học" in trigger["show-sweet-alert"]["text"].lower() or \
               "lịch" in trigger["show-sweet-alert"]["text"].lower()

    def test_generates_correct_number_of_sessions(self, client, staff_user, klass_with_schedule):
        """TC-1: Tạo đúng số buổi học theo lịch tuần + khoảng ngày"""
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import ClassSchedule

        # Đặt khoảng 2 tuần, lịch học 1 ngày/tuần (đúng weekday hôm nay)
        today = date.today()
        klass_with_schedule.start_date = today
        klass_with_schedule.end_date = today + timedelta(days=13)  # 2 tuần
        klass_with_schedule.save()

        schedule = klass_with_schedule.weekly_schedules.first()
        # Đếm số ngày đúng weekday trong khoảng
        expected = sum(
            1 for i in range(14)
            if (today + timedelta(days=i)).weekday() == schedule.day_of_week
        )

        resp = self._post(client, staff_user, klass_with_schedule)
        assert resp.status_code == 200
        created = ClassSession.objects.filter(klass=klass_with_schedule).count()
        assert created == expected

    def test_reuse_existing_planned_sessions(self, client, staff_user, klass_with_schedule):
        """TC-2: Reuse existing PLANNED sessions, không tạo mới trùng lặp"""
        from apps.class_sessions.models import ClassSession

        today = date.today()
        klass_with_schedule.start_date = today
        klass_with_schedule.end_date = today + timedelta(days=13)
        klass_with_schedule.save()

        schedule = klass_with_schedule.weekly_schedules.first()
        # Tìm ngày đầu tiên khớp weekday
        first_session_date = today
        while first_session_date.weekday() != schedule.day_of_week:
            first_session_date += timedelta(days=1)

        # Tạo sẵn 1 session PLANNED
        existing = ClassSession.objects.create(
            klass=klass_with_schedule,
            date=first_session_date,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            status="PLANNED",
            index=1,
        )
        existing_pk = existing.pk

        resp = self._post(client, staff_user, klass_with_schedule)
        assert resp.status_code == 200
        # Session cũ phải được giữ lại (reused), không bị xóa rồi tạo lại với pk mới
        assert ClassSession.objects.filter(pk=existing_pk).exists()

    def test_delete_surplus_sessions(self, client, staff_user, klass_with_schedule):
        """TC-3: Existing sessions dư (ngoài khoảng ngày mới) → bị xóa"""
        from apps.class_sessions.models import ClassSession

        today = date.today()
        klass_with_schedule.start_date = today
        klass_with_schedule.end_date = today + timedelta(days=6)  # 1 tuần
        klass_with_schedule.save()

        schedule = klass_with_schedule.weekly_schedules.first()

        # Tạo session ở ngày rất xa trong tương lai (sẽ dư)
        far_future = today + timedelta(days=60)
        ClassSession.objects.create(
            klass=klass_with_schedule,
            date=far_future,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            status="PLANNED",
            index=99,
        )

        resp = self._post(client, staff_user, klass_with_schedule)
        assert resp.status_code == 200
        # Session ngày xa phải bị xóa
        assert not ClassSession.objects.filter(
            klass=klass_with_schedule, date=far_future
        ).exists()

    def test_lessons_assigned_in_order(self, client, staff_user, klass_with_schedule, lessons):
        """TC-4: Gán Lesson đúng thứ tự module.order → lesson.order"""
        from apps.class_sessions.models import ClassSession

        today = date.today()
        # Đảm bảo khoảng ngày đủ để tạo ít nhất len(lessons) buổi
        # Tìm ngày đầu tiên khớp weekday
        schedule = klass_with_schedule.weekly_schedules.first()
        first_day = today
        while first_day.weekday() != schedule.day_of_week:
            first_day += timedelta(days=1)

        # Tạo end_date đủ để có đúng len(lessons) tuần
        klass_with_schedule.start_date = first_day
        klass_with_schedule.end_date = first_day + timedelta(weeks=len(lessons) + 1)
        klass_with_schedule.save()

        resp = self._post(client, staff_user, klass_with_schedule)
        assert resp.status_code == 200

        sessions = ClassSession.objects.filter(klass=klass_with_schedule).order_by("index")
        # Các buổi đầu phải có lesson theo thứ tự
        for i, lesson in enumerate(lessons):
            assert sessions[i].lesson_id == lesson.pk, \
                f"Buổi {i+1} phải có lesson '{lesson.name}'"

    def test_sessions_beyond_lesson_count_have_no_lesson(self, client, staff_user, klass_with_schedule, lessons):
        """TC-5: Buổi vượt quá số lesson → lesson=None"""
        from apps.class_sessions.models import ClassSession

        schedule = klass_with_schedule.weekly_schedules.first()
        first_day = date.today()
        while first_day.weekday() != schedule.day_of_week:
            first_day += timedelta(days=1)

        # Tạo đủ buổi để vượt quá số lesson (lessons fixture có 3 bài)
        extra_weeks = len(lessons) + 3
        klass_with_schedule.start_date = first_day
        klass_with_schedule.end_date = first_day + timedelta(weeks=extra_weeks)
        klass_with_schedule.save()

        resp = self._post(client, staff_user, klass_with_schedule)
        assert resp.status_code == 200

        sessions = ClassSession.objects.filter(klass=klass_with_schedule).order_by("index")
        total = sessions.count()
        assert total > len(lessons), "Cần có nhiều buổi hơn số lesson để test"

        # Các buổi sau lesson cuối phải lesson=None
        for session in sessions[len(lessons):]:
            assert session.lesson is None, \
                f"Buổi index {session.index} phải không có lesson"

    def test_session_indices_are_sequential_after_generate(self, client, staff_user, klass_with_schedule):
        """TC-8: Index được đánh lại liên tục sau generate"""
        from apps.class_sessions.models import ClassSession

        today = date.today()
        schedule = klass_with_schedule.weekly_schedules.first()
        first_day = today
        while first_day.weekday() != schedule.day_of_week:
            first_day += timedelta(days=1)

        klass_with_schedule.start_date = first_day
        klass_with_schedule.end_date = first_day + timedelta(weeks=3)
        klass_with_schedule.save()

        resp = self._post(client, staff_user, klass_with_schedule)
        assert resp.status_code == 200

        sessions = ClassSession.objects.filter(
            klass=klass_with_schedule
        ).order_by("index")

        indices = [s.index for s in sessions]
        expected = list(range(1, len(indices) + 1))
        assert indices == expected, f"Indices phải liên tục 1..n, got: {indices}"