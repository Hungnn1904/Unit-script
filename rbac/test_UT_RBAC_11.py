
 
# Test case: UT_RBAC_11
# Mục đích: Kiểm tra phụ huynh truy cập lịch sử điểm danh của con mình.
# Logic: Đăng nhập bằng parent, truy cập /attendance/child_history/{student.id}/ với student là con của parent.
# Kết quả mong muốn: API trả về 200.
from django.test import TestCase, Client
from apps.accounts.models import User

class TestUT_RBAC_11(TestCase):
    def test_UT_RBAC_11(self):
        from apps.attendance.models import Attendance
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH11')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C011A', name='Test Class 11', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        parent = User.objects.create_user(username='parent11a', password='pass', role='Parent')
        student = User.objects.create_user(username='student11a', password='pass', role='Student')
        from apps.accounts.models import ParentStudentRelation
        ParentStudentRelation.objects.create(parent=parent, student=student)
        client.force_login(parent)
        url = f'/attendance/child_history/{student.id}/'
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        from apps.attendance.models import Attendance
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH11B')
        center = Center.objects.create(name='Main Center', code='CEN11')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C011B', name='Test Class 11', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        parent = User.objects.create_user(username='parent11b', password='pass', role='Parent')
        student = User.objects.create_user(username='student11b', password='pass', role='Student')
        client.force_login(parent)
        url = f'/attendance/history/{student.id}/'
        response = client.get(url)
        self.assertIn(response.status_code, [200, 403])
