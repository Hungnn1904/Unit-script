 
# Test case: UT_RBAC_09
# Mục đích: Kiểm tra giáo viên thuộc lớp có quyền cập nhật điểm danh cho học sinh trong lớp.
# Logic: Đăng nhập bằng teacher thuộc lớp, gửi request điểm danh.
# Kết quả mong muốn: API trả về 200.
from django.test import TestCase, Client
from apps.accounts.models import User
class TestUT_RBAC_09(TestCase):
    def test_UT_RBAC_09(self):
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        from django.contrib.auth.models import Permission
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH09')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C009A', name='Test Class 9', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        teacher = User.objects.create_user(username='teacher9a', password='pass', role='Teacher')
        klass.teachers.add(teacher)
        perm = Permission.objects.get(codename='change_attendance')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student9a', password='pass', role='Student')
        client.force_login(teacher)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'P'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 200)
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        from django.contrib.auth.models import Permission
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH09B')
        center = Center.objects.create(name='Main Center', code='CEN09')
        room = Room.objects.create(center=center, name='Room 1')
        teacher = User.objects.create_user(username='teacher9b', password='pass', role='Teacher')
        klass = Class.objects.create(code='C009B', name='Test Class 9', center=center, subject=subject, room=room, main_teacher=teacher)
        session = ClassSession.objects.create(klass=klass, index=1)
        perm = Permission.objects.get(codename='change_attendance')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student9b', password='pass', role='Student')
        client.force_login(teacher)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'P'}
        response = client.post(url, data)
        self.assertIn(response.status_code, [200, 204])
