
from django.test import TestCase, Client

class TestUT_RBAC_07(TestCase):
    def test_UT_RBAC_07(self):
        from apps.accounts.models import User
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math')
        center = Center.objects.create(name='Main Center', code='CEN07')
        room = Room.objects.create(center=center, name='Room 1')
        teacher = User.objects.create_user(username='teacher7', password='pass', role='Teacher')
        klass = Class.objects.create(code='C007', name='Test Class 7', center=center, subject=subject, room=room, main_teacher=teacher)
        session = ClassSession.objects.create(klass=klass, index=1)
        client.force_login(teacher)
        url = f'/sessions/{session.id}/detail/'
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
    def test_UT_RBAC_07(self):
        from apps.accounts.models import User
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math')
        center = Center.objects.create(name='Main Center', code='CEN07')
        room = Room.objects.create(center=center, name='Room 1')
        teacher = User.objects.create_user(username='teacher7', password='pass', role='Teacher')
        klass = Class.objects.create(code='C007', name='Test Class 7', center=center, subject=subject, room=room, main_teacher=teacher)
        session = ClassSession.objects.create(klass=klass, index=1)
        client.force_login(teacher)
        url = f'/sessions/{session.id}/detail/'
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
