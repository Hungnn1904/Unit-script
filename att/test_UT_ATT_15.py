from django.test import TestCase, Client

class TestUT_ATT_15(TestCase):
    def test_UT_ATT_15(self):
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
        klass = Class.objects.create(code='C015', name='Test Class 15', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=15)
        student1 = User.objects.create_user(username='student15a', password='pass', role='Student')
        student2 = User.objects.create_user(username='student15b', password='pass', role='Student')
        client.force_login(student1)
        url = f'/assessments/update/{session.id}/{student2.id}/'
        data = {'score': 7}
        response = client.post(url, data)
        self.assertIn(response.status_code, [302, 403])
        if response.status_code == 302:
            self.assertIn('/accounts/login', response.url)
