
# Test case: UT_ATT_13
# Mục đích: Kiểm tra phụ huynh cố gắng cập nhật điểm danh cho học sinh.
# Logic: Đăng nhập bằng parent, gửi request điểm danh.
# Kết quả mong muốn: API trả về 302 (redirect login) hoặc 403 (forbidden).
from django.test import TestCase, Client

class TestUT_ATT_13(TestCase):
    def test_UT_ATT_13(self):
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
        klass = Class.objects.create(code='C013', name='Test Class 13', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=13)
        parent = User.objects.create_user(username='parent1', password='pass', role='Parent')
        student = User.objects.create_user(username='student13', password='pass', role='Student')

        client.force_login(parent)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'P'}
        response = client.post(url, data)
        self.assertIn(response.status_code, [302, 403])
        if response.status_code == 302:
            self.assertIn('/accounts/login', response.url)
