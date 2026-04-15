
from django.test import TestCase, Client
from apps.accounts.models import User

class TestUT_RBAC_16(TestCase):
    def test_UT_RBAC_16(self):
        # Student GET own attendance history → HTTP 200
        client = Client()
        student = User.objects.create_user(username='student16', password='pass', role='Student')
        client.force_login(student)
        url = f'/attendance/history/{student.id}/'
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        client = Client()
        student = User.objects.create_user(username='student16', password='pass', role='Student')
        client.force_login(student)
        url = f'/attendance/history/{student.id}/'
        response = client.get(url)
        self.assertIn(response.status_code, [200, 403])
