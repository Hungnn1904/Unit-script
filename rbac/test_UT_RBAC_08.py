
from django.test import TestCase, Client

class TestUT_RBAC_08(TestCase):
    def test_UT_RBAC_08(self):
        from apps.accounts.models import User
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math')
        center = Center.objects.create(name='Main Center', code='CEN08')
        room = Room.objects.create(center=center, name='Room 1')
        teacher1 = User.objects.create_user(username='teacher8a', password='pass', role='Teacher')
        teacher2 = User.objects.create_user(username='teacher8b', password='pass', role='Teacher')
        klass = Class.objects.create(code='C008', name='Test Class 8', center=center, subject=subject, room=room, main_teacher=teacher1)
        session = ClassSession.objects.create(klass=klass, index=1)
        client.force_login(teacher2)
        url = f'/sessions/{session.id}/detail/'
        response = client.get(url)
        self.assertIn(response.status_code, [403, 404])
        self.assertEqual(response.status_code, 403)
    def test_UT_RBAC_08(self):
        from apps.accounts.models import User
        from apps.class_sessions.models import ClassSession
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math')
        center = Center.objects.create(name='Main Center', code='CEN08')
        room = Room.objects.create(center=center, name='Room 1')
        teacher1 = User.objects.create_user(username='teacher8a', password='pass', role='Teacher')
        teacher2 = User.objects.create_user(username='teacher8b', password='pass', role='Teacher')
        klass = Class.objects.create(code='C008', name='Test Class 8', center=center, subject=subject, room=room, main_teacher=teacher1)
        session = ClassSession.objects.create(klass=klass, index=1)
        client.force_login(teacher2)
        url = f'/sessions/{session.id}/detail/'
        response = client.get(url)
        self.assertIn(response.status_code, [403, 404])
