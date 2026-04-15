
from django.test import TestCase, Client

class TestUT_RBAC_03(TestCase):
    def test_UT_RBAC_03(self):
        from apps.accounts.models import User
        client = Client()
        admin = User.objects.create_superuser(username='admin3', password='pass', role='Admin', email='admin3@example.com')
        client.force_login(admin)
        url = '/accounts/manage/'
        data = {'username': 'newuser', 'password': 'pass', 'role': 'Teacher'}
        response = client.post(url, data)
        self.assertIn(response.status_code, [200, 201])
        self.assertIn(response.status_code, [200, 201])
