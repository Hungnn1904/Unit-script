
# Test case: UT_ATT_03
# Mục đích: Kiểm tra gửi request thiếu trường 'status' khi điểm danh.
# Logic: Tạo dữ liệu, gán quyền, gửi request không có status.
# Kết quả mong muốn: API trả về 400, không lưu dữ liệu.
from django.test import TestCase, Client

class TestUT_ATT_03(TestCase):
    def test_UT_ATT_03(self):
        from apps.attendance.models import Attendance
        from apps.class_sessions.models import ClassSession
        from apps.accounts.models import User
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room

        client = Client()
        subject = Subject.objects.create(name='Math')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C003', name='Test Class 3', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=3)
        teacher = User.objects.create_user(username='teacher3', password='pass', role='Teacher')
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='change_attendance')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student7', password='pass', role='Student')

        client.force_login(teacher)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 400)
