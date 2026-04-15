from django.test import TestCase, Client

class TestUT_ATT_17(TestCase):
    def test_UT_ATT_17(self):
        from apps.assessments.models import Assessment
        from apps.class_sessions.models import ClassSession
        from apps.accounts.models import User
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        from django.contrib.auth.models import Permission
        client = Client()
        subject = Subject.objects.create(name='Math')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C017', name='Test Class 17', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=17)
        teacher = User.objects.create_user(username='teacher17', password='pass', role='Teacher')
        perm = Permission.objects.get(codename='change_assessment')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student17', password='pass', role='Student')
        client.force_login(teacher)
        url = f'/assessments/update/{session.id}/{student.id}/'
        data = {'score': 15}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 400)
        ass = Assessment.objects.filter(session=session, student=student).first()
        self.assertIsNone(ass)
