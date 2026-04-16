
 
# Test case: UT_RBAC_13
# Mục đích: Kiểm tra phụ huynh không được phép cập nhật điểm danh cho con mình.
# Logic: Đăng nhập bằng parent, gửi request điểm danh cho student là con của parent.
# Kết quả mong muốn: API trả về 403.
from django.test import TestCase, Client
from apps.accounts.models import User

class TestUT_RBAC_13(TestCase):
    def test_UT_RBAC_13(self):
        from apps.attendance.models import Attendance
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH13')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C013', name='Test Class 13', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        parent = User.objects.create_user(username='parent13', password='pass', role='Parent')
        student = User.objects.create_user(username='student13', password='pass', role='Student')
        from apps.accounts.models import ParentStudentRelation
        ParentStudentRelation.objects.create(parent=parent, student=student)
        client.force_login(parent)
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
        subject = Subject.objects.create(name='Math', code='MATH13B')
        center = Center.objects.create(name='Main Center', code='CEN13')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C013', name='Test Class 13', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        parent = User.objects.create_user(username='parent13', password='pass', role='Parent')
        student = User.objects.create_user(username='student13', password='pass', role='Student')
        client.force_login(parent)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'P'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 403)
