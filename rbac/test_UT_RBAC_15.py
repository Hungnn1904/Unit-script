
 
# Test case: UT_RBAC_15
# Mục đích: Kiểm tra học sinh không được phép cập nhật điểm danh.
# Logic: Đăng nhập bằng student, gửi request điểm danh.
# Kết quả mong muốn: API trả về 403.
from django.test import TestCase, Client
from apps.accounts.models import User

class TestUT_RBAC_15(TestCase):
    def test_UT_RBAC_15(self):
        # Student cannot POST attendance → HTTP 403
        from apps.attendance.models import Attendance
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH15')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C015', name='Test Class 15', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        student = User.objects.create_user(username='student15', password='pass', role='Student')
        client.force_login(student)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'P'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 403)
        from apps.attendance.models import Attendance
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH15B')
        center = Center.objects.create(name='Main Center', code='CEN15')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C015', name='Test Class 15', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        student = User.objects.create_user(username='student15', password='pass', role='Student')
        client.force_login(student)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'P'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 403)
