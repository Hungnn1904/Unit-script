from django.test import TestCase, Client

class TestUT_ATT_02(TestCase):
    def test_UT_ATT_02(self):
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
        klass = Class.objects.create(code='C002', name='Test Class 2', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=2)
        teacher = User.objects.create_user(username='teacher2', password='pass', role='Teacher')
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='change_attendance')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student6', password='pass', role='Student')

        client.force_login(teacher)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'Sick'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 400)
