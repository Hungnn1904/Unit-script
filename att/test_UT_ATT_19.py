from django.test import TestCase, Client

class TestUT_ATT_19(TestCase):
    def test_UT_ATT_19(self):
        from apps.assessments.models import Assessment
        from apps.class_sessions.models import ClassSession
        from apps.accounts.models import User
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        client = Client()
        subject = Subject.objects.create(name='Math')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C019', name='Test Class 19', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=19)
        parent = User.objects.create_user(username='parent19', password='pass', role='Parent')
        student = User.objects.create_user(username='student19', password='pass', role='Student')
        client.force_login(parent)
        url = f'/assessments/update/{session.id}/{student.id}/'
        data = {'score': 8}
        response = client.post(url, data)
        self.assertIn(response.status_code, [302, 403])
        if response.status_code == 302:
            self.assertIn('/accounts/login', response.url)
