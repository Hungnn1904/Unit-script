
 
# Test case: UT_RBAC_12
# Mục đích: Kiểm tra phụ huynh không được truy cập lịch sử điểm danh của học sinh không phải con mình.
# Logic: Đăng nhập bằng parent, truy cập /attendance/child_history/{student.id}/ với student không phải con của parent.
# Kết quả mong muốn: API trả về 403.
from django.test import TestCase, Client
from apps.accounts.models import User
class TestUT_RBAC_12(TestCase):
    def test_UT_RBAC_12(self):
        from apps.attendance.models import Attendance
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH12')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C012', name='Test Class 12', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        parent = User.objects.create_user(username='parent12', password='pass', role='Parent')
        student1 = User.objects.create_user(username='student12a', password='pass', role='Student')
        student2 = User.objects.create_user(username='student12b', password='pass', role='Student')
        # parent can only view student1, not student2
        from apps.accounts.models import ParentStudentRelation
        ParentStudentRelation.objects.create(parent=parent, student=student1)
        client.force_login(parent)
        url = f'/attendance/child_history/{student2.id}/'
        response = client.get(url)
        self.assertEqual(response.status_code, 403)
        from apps.attendance.models import Attendance
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH12B')
        center = Center.objects.create(name='Main Center', code='CEN12')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C012', name='Test Class 12', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        parent = User.objects.create_user(username='parent12', password='pass', role='Parent')
        student1 = User.objects.create_user(username='student12a', password='pass', role='Student')
        student2 = User.objects.create_user(username='student12b', password='pass', role='Student')
        client.force_login(parent)
        url = f'/attendance/history/{student2.id}/'
        response = client.get(url)
        self.assertIn(response.status_code, [403, 404])
