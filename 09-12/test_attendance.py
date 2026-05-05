from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Permission
from apps.accounts.models import User
from apps.centers.models import Center
from apps.curriculum.models import Subject
from apps.classes.models import Class
from apps.class_sessions.models import ClassSession
from apps.enrollments.models import Enrollment, EnrollmentStatus
from apps.attendance.models import Attendance
import datetime

class AttendancePendingTests(TestCase):
    def setUp(self):
        # Setup basic data
        self.center = Center.objects.create(name="Test Center")
        self.subject = Subject.objects.create(name="Test Subject")
        
        self.admin = User.objects.create_superuser(username="admin_user", password="password", email="admin@test.com")
        self.assistant = User.objects.create_user(username="assistant", password="password", role="ASSISTANT")
        self.staff = User.objects.create_user(username="staff_user", password="password", role="STAFF")
        
        self.teacher = User.objects.create_user(username="teacher", password="password", role="TEACHER")
        self.student = User.objects.create_user(username="student", password="password", role="STUDENT")

        self.klass = Class.objects.create(
            name="Test Class",
            center=self.center,
            subject=self.subject,
            main_teacher=self.teacher,
            status="ONGOING"
        )
        self.session = ClassSession.objects.create(
            klass=self.klass,
            index=1,
            date=datetime.date.today()
        )
        self.enrollment = Enrollment.objects.create(
            klass=self.klass,
            student=self.student,
            status=EnrollmentStatus.ACTIVE,
            fee_per_session=100000,
            sessions_purchased=10
        )
        
        self.change_perm = Permission.objects.get(codename="change_attendance")
        self.client = Client()

    def test_tc_f09_rb_03_assistant_can_mark_attendance(self):
        """TC_F09_RB_03: Assistant Teacher can mark attendance"""
        self.assistant.user_permissions.add(self.change_perm)
        self.client.login(username="assistant", password="password")
        
        url = reverse("attendance:update_attendance", args=[self.session.id, self.student.id])
        response = self.client.post(url, {"status": "P", "note": "Assistant marked"})
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Attendance.objects.filter(session=self.session, student=self.student, status="P").exists())

    def test_tc_f09_rb_04_admin_can_mark_attendance(self):
        """TC_F09_RB_04: Admin can mark attendance"""
        # Admin usually has all perms, but we'll be explicit if needed. 
        # Superuser doesn't need explicit perms in Django's has_perm.
        self.client.login(username="admin_user", password="password")
        
        url = reverse("attendance:update_attendance", args=[self.session.id, self.student.id])
        response = self.client.post(url, {"status": "P", "note": "Admin marked"})
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Attendance.objects.filter(session=self.session, student=self.student, status="P").exists())

    def test_tc_f09_rb_05_unprivileged_staff_cannot_update(self):
        """TC_F09_RB_05: Unprivileged staff cannot update attendance"""
        # Staff user does NOT have change_attendance permission
        self.client.login(username="staff_user", password="password")
        
        url = reverse("attendance:update_attendance", args=[self.session.id, self.student.id])
        response = self.client.post(url, {"status": "P", "note": "Staff attempted"})
        
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Attendance.objects.filter(session=self.session, student=self.student).exists())

    def test_tc_f09_nt_03_non_existent_session(self):
        """TC_F09_NT_03: Attempt attendance for non-existent session"""
        self.admin.user_permissions.add(self.change_perm)
        self.client.login(username="admin_user", password="password")
        
        url = reverse("attendance:update_attendance", args=[9999, self.student.id])
        response = self.client.post(url, {"status": "P"})
        
        self.assertEqual(response.status_code, 404)

    def test_tc_f09_nt_04_non_existent_student(self):
        """TC_F09_NT_04: Attempt attendance for non-existent student"""
        self.admin.user_permissions.add(self.change_perm)
        self.client.login(username="admin_user", password="password")
        
        url = reverse("attendance:update_attendance", args=[self.session.id, 9999])
        response = self.client.post(url, {"status": "P"})
        
        self.assertEqual(response.status_code, 404)

    def test_tc_f09_nt_05_invalid_status(self):
        """TC_F09_NT_05: Attempt attendance with invalid status"""
        self.admin.user_permissions.add(self.change_perm)
        self.client.login(username="admin_user", password="password")
        
        url = reverse("attendance:update_attendance", args=[self.session.id, self.student.id])
        response = self.client.post(url, {"status": "X", "note": "Invalid status"})
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Attendance.objects.filter(session=self.session, student=self.student).exists())
