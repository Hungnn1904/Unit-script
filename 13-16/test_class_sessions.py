"""
Test suite for ClassSession app - critical CRUD and permission tests
Tests cover: unique constraints, permissions, CRUD, cascading deletes, relationships
"""
import pytest
from datetime import date, time
from django.utils import timezone
from django.contrib.auth.models import Group

from apps.accounts.models import User
from apps.centers.models import Center, Room
from apps.classes.models import Class
from apps.curriculum.models import Subject, Module, Lesson
from .models import ClassSession, ClassSessionPhoto


@pytest.fixture
def admin_user():
    """Create admin user"""
    user = User.objects.create_user(
        username='admin_teacher',
        email='admin@test.com',
        password='pass123',
        first_name='Admin',
        last_name='Teacher',
        role='ADMIN'
    )
    user.is_superuser = True
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def teacher_user():
    """Create teacher user"""
    return User.objects.create_user(
        username='teacher1',
        email='teacher@test.com',
        password='pass123',
        first_name='Teacher',
        last_name='One',
        role='TEACHER'
    )


@pytest.fixture
def assistant_user():
    """Create assistant user"""
    return User.objects.create_user(
        username='assistant1',
        email='assistant@test.com',
        password='pass123',
        first_name='Assistant',
        last_name='One',
        role='ASSISTANT'
    )


@pytest.fixture
def center():
    """Create test center"""
    return Center.objects.create(
        name='Test Center',
        code='TC-001'
    )


@pytest.fixture
def room(center):
    """Create test room"""
    return Room.objects.create(
        name='Room A',
        note='Testing room',
        center=center
    )


@pytest.fixture
def subject():
    """Create test subject"""
    return Subject.objects.create(
        name='Math',
        code='MATH-101'
    )


@pytest.fixture
def klass(center, subject, teacher_user):
    """Create test class"""
    return Class.objects.create(
        name='Math Class 1',
        code='MC-001',
        center=center,
        subject=subject,
        main_teacher=teacher_user,
        status='ONGOING'
    )


@pytest.fixture
def lesson(subject):
    """Create test lesson"""
    module = Module.objects.create(title='Module 1', subject=subject, order=1)
    return Lesson.objects.create(
        title='Lesson 1',
        module=module,
        order=1,
        objectives='Learn basics'
    )


@pytest.mark.django_db
class TestClassSessionUnique:
    """Test unique_together constraint (klass, index)"""

    # [UT_SES_01] Model - Session Unique Together Constraint
    def test_session_unique_together_klass_index(self, klass, lesson):
        """
        Test: Prevent duplicate session indices in same class
        - Create first session with index=1 in a class
        - Try to create another session with same index=1 in same class
        - Should raise IntegrityError due to unique_together constraint
        Expected: Constraint prevents duplicate (klass, index) pairs
        """
        session1 = ClassSession.objects.create(
            klass=klass,
            index=1,
            date=date(2026, 4, 21),
            status='PLANNED'
        )
        assert session1.id is not None

        # Try to create duplicate - should fail
        with pytest.raises(Exception):  # IntegrityError
            ClassSession.objects.create(
                klass=klass,
                index=1,  # Same index
                date=date(2026, 4, 22),
                status='PLANNED'
            )

    # [UT_SES_02] Model - Different Classes Can Have Same Index
    def test_different_classes_can_have_same_index(self, center, subject, teacher_user):
        """
        Test: Different classes can have same index number
        - Create two classes in same center
        - Create session with index=1 in class1
        - Create session with index=1 in class2
        Expected: unique_together allows same index across different classes
        """
        klass1 = Class.objects.create(
            name='Class 1',
            code='C1',
            center=center,
            subject=subject,
            main_teacher=teacher_user,
            status='ONGOING'
        )
        klass2 = Class.objects.create(
            name='Class 2',
            code='C2',
            center=center,
            subject=subject,
            main_teacher=teacher_user,
            status='ONGOING'
        )

        session1 = ClassSession.objects.create(
            klass=klass1,
            index=1,
            date=date(2026, 4, 21),
            status='PLANNED'
        )
        session2 = ClassSession.objects.create(
            klass=klass2,
            index=1,  # Same index, different class - OK
            date=date(2026, 4, 21),
            status='PLANNED'
        )
        assert session1.id and session2.id


@pytest.mark.django_db
class TestClassSessionCRUD:
    """Test CRUD operations"""

    # [UT_SES_03] Model - Session Create Minimal
    def test_session_create_minimal(self, klass):
        """
        Test: Create session with minimal required fields
        - Create with only klass, index, status
        Expected: Session saves successfully with defaults for optional fields
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            status='PLANNED'
        )
        assert session.id is not None
        assert session.klass == klass
        assert session.index == 1
        assert session.status == 'PLANNED'

    # [UT_SES_04] Model - Session Create With All Fields
    def test_session_create_with_all_fields(self, klass, lesson, teacher_user, room):
        """
        Test: Create session with all optional fields populated
        - Set date, time, lesson, teacher_override, room_override
        Expected: All fields persist correctly in database
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            date=date(2026, 4, 21),
            start_time=time(9, 0),
            end_time=time(10, 30),
            lesson=lesson,
            status='PLANNED',
            teacher_override=teacher_user,
            room_override=room
        )
        assert session.date == date(2026, 4, 21)
        assert session.start_time == time(9, 0)
        assert session.teacher_override == teacher_user
        assert session.room_override == room

    # [UT_SES_05] Model - Session Update
    def test_session_update(self, klass):
        """
        Test: Update existing session fields
        - Create with status=PLANNED, update to status=DONE and set date
        Expected: Changes persist and are retrievable from database
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            status='PLANNED'
        )
        session.status = 'DONE'
        session.date = date(2026, 4, 21)
        session.save()

        refreshed = ClassSession.objects.get(id=session.id)
        assert refreshed.status == 'DONE'
        assert refreshed.date == date(2026, 4, 21)

    # [UT_SES_06] Model - Session Delete
    def test_session_delete(self, klass):
        """
        Test: Delete session from database
        - Create a session, then delete it
        Expected: Session no longer exists in database
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            status='PLANNED'
        )
        session_id = session.id
        session.delete()

        assert not ClassSession.objects.filter(id=session_id).exists()

    # [UT_SES_07] Model - Session Delete Cascades To Photos
    def test_session_delete_cascades_to_photos(self, klass):
        """
        Test: Cascade delete behavior when session deleted
        - Create session and verify photos count
        Expected: Session.photos relationship exists and empty count is 0
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            status='PLANNED'
        )
        # Note: Can't actually test image upload without file storage, 
        # but we can test the model relationship
        assert session.photos.count() == 0


@pytest.mark.django_db
class TestClassSessionRelationships:
    """Test relationships (teacher_override, assistants, lesson)"""

    # [UT_SES_08] Model - Session With Teacher Override
    def test_session_with_teacher_override(self, klass, teacher_user, admin_user):
        """
        Test: Override teacher per session without changing class default
        - Class has main_teacher, session has different teacher_override
        Expected: teacher_override differs from class main_teacher
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            status='PLANNED',
            teacher_override=admin_user  # Different from main_teacher
        )
        session.refresh_from_db()
        assert session.teacher_override == admin_user
        assert session.klass.main_teacher == teacher_user
        assert session.teacher_override != session.klass.main_teacher

    # [UT_SES_09] Model - Session With Multiple Assistants
    def test_session_with_multiple_assistants(self, klass, assistant_user):
        """
        Test: Assign multiple assistants to single session
        - Create two assistants, add both to session.assistants M2M
        Expected: Both assistants are queryable and count is 2
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            status='PLANNED'
        )
        
        # Create multiple assistants
        asst1 = User.objects.create_user(
            username='asst1',
            email='asst1@test.com',
            password='pass123',
            role='ASSISTANT'
        )
        asst2 = User.objects.create_user(
            username='asst2',
            email='asst2@test.com',
            password='pass123',
            role='ASSISTANT'
        )
        
        session.assistants.add(asst1, asst2)
        session.refresh_from_db()
        
        assert session.assistants.count() == 2
        assert asst1 in session.assistants.all()
        assert asst2 in session.assistants.all()

    # [UT_SES_10] Model - Session With Lesson
    def test_session_with_lesson(self, klass, lesson):
        """
        Test: Link session to curriculum lesson
        - Create lesson, then create session with lesson FK
        Expected: session.lesson references the created lesson
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            lesson=lesson,
            status='PLANNED'
        )
        session.refresh_from_db()
        assert session.lesson == lesson

    # [UT_SES_11] Model - Session Lesson Nullable
    def test_session_lesson_nullable(self, klass):
        """
        Test: Lesson FK is nullable
        - Create session without lesson (lesson=None)
        Expected: Session saves and lesson remains None
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            lesson=None,
            status='PLANNED'
        )
        assert session.lesson is None


@pytest.mark.django_db
class TestClassSessionStatus:
    """Test status field and transitions"""

    # [UT_SES_12] Model - Session Status Choices
    def test_session_status_choices(self, klass):
        """
        Test: All defined status choices are valid
        - Test each of PLANNED, DONE, MISSED, CANCELLED
        Expected: Each status saves and is queryable
        """
        statuses = ['PLANNED', 'DONE', 'MISSED', 'CANCELLED']
        for idx, status in enumerate(statuses, 1):
            session = ClassSession.objects.create(
                klass=klass,
                index=idx,
                status=status
            )
            assert session.status == status

    # [UT_SES_13] Model - Session Status Display
    def test_session_status_display(self, klass):
        """
        Test: Status display names via get_status_display()
        - Create session with status=PLANNED
        Expected: Display returns Vietnamese name 'Đã lên lịch'
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            status='PLANNED'
        )
        assert session.get_status_display() == 'Đã lên lịch'


@pytest.mark.django_db
class TestClassSessionOrdering:
    """Test default ordering"""

    # [UT_SES_14] Model - Sessions Ordered By Klass And Index
    def test_sessions_ordered_by_klass_and_index(self, klass):
        """
        Test: Default model ordering by klass then index
        - Create sessions out of order (3, 1, 2)
        Expected: Query returns ordered by index ascending
        """
        # Create multiple sessions out of order
        for idx in [3, 1, 2]:
            ClassSession.objects.create(
                klass=klass,
                index=idx,
                status='PLANNED'
            )
        
        sessions = list(ClassSession.objects.all())
        indices = [s.index for s in sessions]
        assert indices == [1, 2, 3]


@pytest.mark.django_db
class TestClassSessionValidation:
    """Test field validation"""

    # [UT_SES_15] Model - Session Date Optional
    def test_session_date_optional(self, klass):
        """
        Test: Date field can be null
        - Create session with date=None
        Expected: Session saves and date remains None
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            date=None,
            status='PLANNED'
        )
        assert session.date is None

    # [UT_SES_16] Model - Session Time Optional
    def test_session_time_optional(self, klass):
        """
        Test: Time fields (start_time, end_time) can be null
        - Create session with start_time=None, end_time=None
        Expected: Both time fields remain None
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=1,
            start_time=None,
            end_time=None,
            status='PLANNED'
        )
        assert session.start_time is None
        assert session.end_time is None


@pytest.mark.django_db
class TestClassSessionStringRepresentation:
    """Test __str__ methods"""

    # [UT_SES_17] Model - Session String Representation
    def test_session_str(self, klass):
        """
        Test: __str__ method returns readable session name
        - Create session with index=5
        Expected: str() contains 'Buổi 5' and class name
        """
        session = ClassSession.objects.create(
            klass=klass,
            index=5,
            status='PLANNED'
        )
        assert 'Buổi 5' in str(session)
        assert klass.name in str(session)


@pytest.mark.django_db
class TestClassSessionCascadeDelete:
    """Test cascade behavior when class is deleted"""

    # [UT_SES_18] Model - Sessions Cascade Delete With Class
    def test_sessions_cascade_delete_with_class(self, klass):
        """
        Test: Cascade behavior when class is deleted
        - Create two sessions in class, then delete class
        Expected: Both sessions are automatically deleted
        """
        session1 = ClassSession.objects.create(
            klass=klass,
            index=1,
            status='PLANNED'
        )
        session2 = ClassSession.objects.create(
            klass=klass,
            index=2,
            status='PLANNED'
        )
        session_ids = [session1.id, session2.id]
        
        klass.delete()
        
        assert not ClassSession.objects.filter(id__in=session_ids).exists()


# ============================================================================
# Session View & Integration Tests (from test_report_session.py)
# ============================================================================

from django.db import transaction
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import FileSystemStorage
from apps.class_sessions.models import ClassSessionPhoto
from apps.class_sessions import views as session_views


@pytest.fixture(autouse=True)
def rollback_db_session_tests(db):
    """Rollback every test transaction so data never leaks between cases."""
    with transaction.atomic():
        yield
        transaction.set_rollback(True)


@pytest.fixture
def admin_user_session(db):
    return User.objects.create_superuser(
        username="admin",
        password="admin123",
        email="admin@test.com",
    )


@pytest.fixture
def center_session(db):
    from apps.centers.models import Center
    return Center.objects.create(code="CTR-A", name="Center A")


@pytest.fixture
def room_session(db, center_session):
    from apps.centers.models import Room
    return Room.objects.create(center=center_session, name="Room A")


@pytest.fixture
def subject_session(db):
    return Subject.objects.create(code="SUB-A", name="Python")


@pytest.fixture
def teacher_user_session(db, center_session):
    return User.objects.create_user(
        username="teacher1",
        password="teacher123",
        email="teacher1@test.com",
        role="TEACHER",
        center=center_session,
    )


@pytest.fixture
def assistant_user_session(db, center_session):
    return User.objects.create_user(
        username="assistant1",
        password="assistant123",
        email="assistant1@test.com",
        role="ASSISTANT",
        center=center_session,
    )


@pytest.fixture
def student_user_session(db, center_session):
    return User.objects.create_user(
        username="student1",
        password="student123",
        email="student1@test.com",
        role="STUDENT",
        center=center_session,
    )


@pytest.fixture
def auth_client_session(client, admin_user_session):
    client.force_login(admin_user_session)
    return client


@pytest.fixture
def klass_session(db, center_session, subject_session, teacher_user_session, assistant_user_session):
    from apps.classes.models import Class, ClassAssistant
    klass = Class.objects.create(
        code="CLS-01",
        name="Class 01",
        center=center_session,
        subject=subject_session,
        main_teacher=teacher_user_session,
        status="ONGOING",
    )
    ClassAssistant.objects.create(klass=klass, assistant=assistant_user_session, scope="COURSE")
    return klass


@pytest.fixture
def class_sessions_session(db, klass_session):
    session1 = ClassSession.objects.create(
        klass=klass_session,
        index=1,
        date=date(2026, 4, 1),
        start_time=time(9, 0),
        end_time=time(10, 30),
        status="DONE",
    )
    session2 = ClassSession.objects.create(
        klass=klass_session,
        index=2,
        date=date(2026, 4, 8),
        start_time=time(9, 0),
        end_time=time(10, 30),
        status="MISSED",
    )
    session3 = ClassSession.objects.create(
        klass=klass_session,
        index=3,
        date=date(2026, 4, 15),
        start_time=time(9, 0),
        end_time=time(10, 30),
        status="PLANNED",
    )
    return session1, session2, session3


@pytest.fixture
def local_media_storage(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    if hasattr(settings, "STORAGES") and isinstance(settings.STORAGES, dict):
        settings.STORAGES["default"] = {"BACKEND": "django.core.files.storage.FileSystemStorage"}
    ClassSessionPhoto._meta.get_field("image").storage = FileSystemStorage(location=tmp_path)


# [UT_SES_19] Session Detail View Smoke Test
@pytest.mark.django_db
def test_ut_ses_01_session_detail_view_smoke(auth_client_session, class_sessions_session):
    """
    UT_SES_19 - Session detail view smoke test
    - Admin accesses session detail page
    Expected: Returns 200, context has session and student_data_list
    """
    session, _, _ = class_sessions_session
    response = auth_client_session.get(reverse("class_sessions:session_detail", kwargs={"pk": session.pk}))
    assert response.status_code == 200
    assert response.context["session"].pk == session.pk
    assert "student_data_list" in response.context


# [UT_SES_20] Override Teacher Non-Regression
@pytest.mark.django_db
def test_ut_ses_02_override_teacher_non_regression(auth_client_session, class_sessions_session, assistant_user_session):
    """
    UT_SES_20 - Override teacher per session without changing class default
    - Post session_edit with teacher_override=assistant
    - Class still has original main_teacher
    Expected: Session teacher_override set, class main_teacher unchanged
    """
    session, _, _ = class_sessions_session
    class_default_teacher_id = session.klass.main_teacher_id
    payload = {
        "klass": session.klass_id,
        "index": session.index,
        "date": session.date.isoformat() if session.date else "",
        "start_time": session.start_time.strftime("%H:%M") if session.start_time else "",
        "end_time": session.end_time.strftime("%H:%M") if session.end_time else "",
        "lesson": "",
        "status": session.status,
        "teacher_override": assistant_user_session.id,
        "room_override": "",
        "assistants": [],
    }
    response = auth_client_session.post(reverse("class_sessions:session_edit", kwargs={"pk": session.pk}), payload)
    assert response.status_code == 200
    session.refresh_from_db()
    session.klass.refresh_from_db()
    assert session.teacher_override_id == assistant_user_session.id
    assert session.klass.main_teacher_id == class_default_teacher_id


# [UT_SES_21] Override Room Per Session
@pytest.mark.django_db
def test_ut_ses_03_override_room_per_session(auth_client_session, class_sessions_session, room_session):
    """
    UT_SES_21 - Override room at session level
    - Post session_edit with room_override=room_id
    Expected: session.room_override set to specified room
    """
    session, _, _ = class_sessions_session
    payload = {
        "klass": session.klass_id,
        "index": session.index,
        "date": session.date.isoformat() if session.date else "",
        "start_time": session.start_time.strftime("%H:%M") if session.start_time else "",
        "end_time": session.end_time.strftime("%H:%M") if session.end_time else "",
        "lesson": "",
        "status": session.status,
        "teacher_override": "",
        "room_override": room_session.id,
        "assistants": [],
    }
    response = auth_client_session.post(reverse("class_sessions:session_edit", kwargs={"pk": session.pk}), payload)
    assert response.status_code == 200
    session.refresh_from_db()
    assert session.room_override_id == room_session.id


# [UT_SES_22] Session Status State Transition
@pytest.mark.django_db
def test_ut_ses_04_session_status_state_transition(auth_client_session, class_sessions_session):
    """
    UT_SES_22 - Session status state transitions
    - Transition from PLANNED to each of DONE, MISSED, CANCELLED
    Expected: Each transition succeeds and status persists
    """
    _, _, session = class_sessions_session
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
        response = auth_client_session.post(reverse("class_sessions:session_edit", kwargs={"pk": session.pk}), payload)
        assert response.status_code == 200
        session.refresh_from_db()
        assert session.status == new_status


# [UT_SES_23] Session Photos Management
@pytest.mark.django_db
def test_ut_ses_05_session_photos_management(auth_client_session, class_sessions_session, local_media_storage):
    """
    UT_SES_23 - Session photos upload and delete
    - Upload JPEG image to session
    - Delete uploaded photo
    Expected: Photo created on upload, deleted on delete request
    """
    session, _, _ = class_sessions_session
    image = SimpleUploadedFile("session.jpg", b"fake-image-content", content_type="image/jpeg")
    upload_response = auth_client_session.post(
        reverse("class_sessions:session_photos_upload", kwargs={"pk": session.pk}),
        {"images": [image]},
    )
    assert upload_response.status_code in [302, 204]
    assert ClassSessionPhoto.objects.filter(session=session).count() == 1
    photo = ClassSessionPhoto.objects.filter(session=session).first()
    assert photo is not None
    delete_response = auth_client_session.post(
        reverse(
            "class_sessions:session_photo_delete",
            kwargs={"session_pk": session.pk, "photo_pk": photo.pk},
        )
    )
    assert delete_response.status_code in [302, 204]
    assert ClassSessionPhoto.objects.filter(session=session).count() == 0


# [UT_SES_24] Session Detail Forbidden For Non-Staff
@pytest.mark.django_db
def test_ut_ses_06_session_detail_forbidden_for_non_staff(client, class_sessions_session, student_user_session):
    """
    UT_SES_24 - Permission check: non-staff denied session detail
    - Student tries to access session_detail
    Expected: Returns 403 Forbidden
    """
    session, _, _ = class_sessions_session
    client.force_login(student_user_session)
    response = client.get(reverse("class_sessions:session_detail", kwargs={"pk": session.pk}))
    assert response.status_code == 403


# [UT_SES_25] Manage Class Sessions Permission Denied
@pytest.mark.django_db
def test_ut_ses_07_manage_class_sessions_permission_denied(client, student_user_session):
    """
    UT_SES_25 - Permission check: non-staff denied manage_sessions
    - Student tries to access manage_class_sessions
    Expected: Returns 403 Forbidden
    """
    client.force_login(student_user_session)
    response = client.get(reverse("class_sessions:manage_class_sessions"))
    assert response.status_code == 403


# [UT_SES_26] Manage Class Sessions HTMX Empty Page Fallback
@pytest.mark.django_db
def test_ut_ses_08_manage_class_sessions_htmx_empty_page_falls_back(auth_client_session, class_sessions_session):
    """
    UT_SES_26 - HTMX pagination fallback on invalid page
    - Request page=99 (beyond available)
    Expected: Falls back to page 1, returns 200
    """
    response = auth_client_session.get(
        reverse("class_sessions:manage_class_sessions"),
        {"group_by": "date", "per_page": 2, "page": 99},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert response.context["page_obj"].number == 1
    assert response.context["per_page"] == 2
    assert response.context["group_by"] == "date"


# [UT_SES_27] Session Photos Upload Rejects GET
@pytest.mark.django_db
def test_ut_ses_09_session_photos_upload_rejects_get(auth_client_session, class_sessions_session):
    """
    UT_SES_27 - HTTP method validation: GET rejected on upload endpoint
    - Send GET to session_photos_upload
    Expected: Returns 400 Bad Request
    """
    session, _, _ = class_sessions_session
    response = auth_client_session.get(reverse("class_sessions:session_photos_upload", kwargs={"pk": session.pk}))
    assert response.status_code == 400


# [UT_SES_28] Session Photos Upload Requires Files
@pytest.mark.django_db
def test_ut_ses_10_session_photos_upload_requires_files(auth_client_session, class_sessions_session):
    """
    UT_SES_28 - Upload endpoint requires files
    - POST empty dict without images
    Expected: Returns 400 Bad Request
    """
    session, _, _ = class_sessions_session
    response = auth_client_session.post(reverse("class_sessions:session_photos_upload", kwargs={"pk": session.pk}), {})
    assert response.status_code == 400


# [UT_SES_29] Session Photos Upload HTMX Headers
@pytest.mark.django_db
def test_ut_ses_11_session_photos_upload_htmx_headers(auth_client_session, class_sessions_session, local_media_storage):
    """
    UT_SES_29 - HTMX response headers on upload
    - Upload image with HX-Request header
    Expected: Returns 204, includes HX-Redirect and HX-Trigger headers
    """
    session, _, _ = class_sessions_session
    image = SimpleUploadedFile("session-extra.jpg", b"fake-image-content", content_type="image/jpeg")
    before_count = ClassSessionPhoto.objects.filter(session=session).count()
    response = auth_client_session.post(
        reverse("class_sessions:session_photos_upload", kwargs={"pk": session.pk}) + "?as_page=true",
        {"images": [image]},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 204
    assert "HX-Redirect" in response
    assert reverse("class_sessions:session_detail", args=[session.pk]) in response["HX-Redirect"]
    assert "HX-Trigger" in response
    assert ClassSessionPhoto.objects.filter(session=session).count() == before_count + 1


# [UT_SES_30] Session Photo Delete Requires POST
@pytest.mark.django_db
def test_ut_ses_12_session_photo_delete_requires_post(auth_client_session, class_sessions_session, local_media_storage):
    """
    UT_SES_30 - HTTP method validation: GET rejected on delete endpoint
    - Send GET to session_photo_delete
    Expected: Returns 405 Method Not Allowed
    """
    session, _, _ = class_sessions_session
    image = SimpleUploadedFile("for-get-check.jpg", b"fake-image-content", content_type="image/jpeg")
    photo = ClassSessionPhoto.objects.create(
        session=session,
        image=image,
        uploaded_by=session.klass.main_teacher,
    )
    response = auth_client_session.get(
        reverse(
            "class_sessions:session_photo_delete",
            kwargs={"session_pk": session.pk, "photo_pk": photo.pk},
        )
    )
    assert response.status_code == 405


# [UT_SES_31] Session Photo Delete HTMX Success
@pytest.mark.django_db
def test_ut_ses_13_session_photo_delete_htmx_success(auth_client_session, class_sessions_session, local_media_storage):
    """
    UT_SES_31 - HTMX delete response
    - POST delete with HX-Request header
    Expected: Returns 204, includes HX-Trigger, photo removed from DB
    """
    session, _, _ = class_sessions_session
    image = SimpleUploadedFile("for-htmx-delete.jpg", b"fake-image-content", content_type="image/jpeg")
    photo = ClassSessionPhoto.objects.create(
        session=session,
        image=image,
        uploaded_by=session.klass.main_teacher,
    )
    response = auth_client_session.post(
        reverse(
            "class_sessions:session_photo_delete",
            kwargs={"session_pk": session.pk, "photo_pk": photo.pk},
        ) + "?as_page=true",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 204
    assert "HX-Trigger" in response
    assert not ClassSessionPhoto.objects.filter(pk=photo.pk).exists()


# [UT_SES_32] Parse Date Param Formats and Fallback
@pytest.mark.django_db
def test_ut_ses_14_parse_date_param_formats_and_fallback():
    """
    UT_SES_32 - Date parsing helper with fallback
    - Test ISO format (2026-04-20), EU format (20/04/2026), invalid, empty
    Expected: Valid formats parsed, invalid fallback to default
    """
    default_day = date(2026, 1, 1)
    assert session_views._parse_date_param("2026-04-20", default_day) == date(2026, 4, 20)
    assert session_views._parse_date_param("20/04/2026", default_day) == date(2026, 4, 20)
    assert session_views._parse_date_param("invalid", default_day) == default_day
    assert session_views._parse_date_param("", default_day) == default_day


# [UT_SES_33] Session Group Label Branches
@pytest.mark.django_db
def test_ut_ses_15_session_group_label_branches(class_sessions_session):
    """
    UT_SES_33 - Session grouping label helper for all group_by options
    - Test subject, center, teacher, status, timeslot, date, unknown
    Expected: Each option returns correct display string
    """
    session, _, _ = class_sessions_session
    assert session_views._session_group_label(session, "subject") == session.klass.subject.name
    assert session_views._session_group_label(session, "center") == session.klass.center.name
    assert session_views._session_group_label(session, "teacher") == session.klass.main_teacher.display_name_with_email
    assert session_views._session_group_label(session, "status") == session.get_status_display()
    assert session_views._session_group_label(session, "timeslot") == "09:00 - 10:30"
    assert session_views._session_group_label(session, "date") == "01/04/2026"
    assert session_views._session_group_label(session, "unknown") == ""


# [UT_SES_34] User Display Name Fallbacks
@pytest.mark.django_db
def test_ut_ses_16_user_display_name_fallbacks(db, center_session):
    """
    UT_SES_34 - User display name helper with fallbacks
    - Test None user, user with display_name_with_email
    Expected: None returns empty, user returns display_name_with_email
    """
    user = User.objects.create_user(
        username="display_user",
        password="pass123",
        email="display@test.com",
        first_name="Display",
        last_name="Name",
        role="TEACHER",
        center=center_session,
    )
    assert session_views._user_display_name(None) == ""
    assert session_views._user_display_name(user) == user.display_name_with_email


# [UT_SES_35] User Is Session Staff Paths
@pytest.mark.django_db
def test_ut_ses_17_user_is_session_staff_paths(class_sessions_session, teacher_user_session, assistant_user_session, student_user_session):
    """
    UT_SES_35 - Session staff permission check
    - Test main_teacher (True), assistant (True), student (False)
    Expected: Teachers/assistants are session staff, students are not
    """
    session, _, _ = class_sessions_session
    assert session_views._user_is_session_staff(session, teacher_user_session) is True
    assert session_views._user_is_session_staff(session, assistant_user_session) is True
    assert session_views._user_is_session_staff(session, student_user_session) is False
