from django.test import TestCase, Client

class TestUT_ATT_06(TestCase):
    def test_UT_ATT_06(self):
        from apps.accounts.models import User
        client = Client()
        teacher = User.objects.create_user(username='teacher6', password='pass', role='Teacher')
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='change_attendance')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student10', password='pass', role='Student')
        client.force_login(teacher)
        url = f'/attendance/update/9999/{student.id}/'
        data = {'status': 'P'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 404)
