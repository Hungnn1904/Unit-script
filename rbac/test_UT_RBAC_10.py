from django.test import TestCase, Client
from apps.accounts.models import User
class TestUT_RBAC_10(TestCase):
    def test_UT_RBAC_10(self):
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        from django.contrib.auth.models import Permission
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH10')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C010', name='Test Class 10', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        teacher1 = User.objects.create_user(username='teacher10a', password='pass', role='Teacher')
        teacher2 = User.objects.create_user(username='teacher10b', password='pass', role='Teacher')
        klass.teachers.add(teacher1)
        perm = Permission.objects.get(codename='change_attendance')
        teacher2.user_permissions.add(perm)
        teacher2.save()
        student = User.objects.create_user(username='student10', password='pass', role='Student')
        client.force_login(teacher2)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'P'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 403)
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        from django.contrib.auth.models import Permission
        client = Client()
        subject = Subject.objects.create(name='Math', code='MATH10B')
        center = Center.objects.create(name='Main Center', code='CEN10')
        room = Room.objects.create(center=center, name='Room 1')
        teacher1 = User.objects.create_user(username='teacher10a', password='pass', role='Teacher')
        teacher2 = User.objects.create_user(username='teacher10b', password='pass', role='Teacher')
        klass = Class.objects.create(code='C010', name='Test Class 10', center=center, subject=subject, room=room, main_teacher=teacher1)
        session = ClassSession.objects.create(klass=klass, index=1)
        perm = Permission.objects.get(codename='change_attendance')
        teacher2.user_permissions.add(perm)
        teacher2.save()
        student = User.objects.create_user(username='student10', password='pass', role='Student')
        client.force_login(teacher2)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'P'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 403)
