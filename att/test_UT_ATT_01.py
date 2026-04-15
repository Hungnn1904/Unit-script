from django.test import TestCase, Client

class TestUT_ATT_01(TestCase):
    def test_UT_ATT_01(self):
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
        klass = Class.objects.create(code='C001', name='Test Class', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=1)
        teacher = User.objects.create_user(username='teacher', password='pass', role='Teacher')
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='change_attendance')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student5', password='pass', role='Student')

        client.force_login(teacher)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'P'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 200)
        att = Attendance.objects.filter(session=session, student=student).first()
        self.assertIsNotNone(att)
        self.assertEqual(att.status, 'P')
