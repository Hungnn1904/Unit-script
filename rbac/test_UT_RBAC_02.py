
from django.test import TestCase, Client

class TestUT_RBAC_02(TestCase):
    def test_UT_RBAC_02(self):
        from apps.accounts.models import User
        client = Client()
        admin = User.objects.create_superuser(username='admin2', password='pass', role='Admin', email='admin2@example.com')
        client.force_login(admin)
        url = '/classes/manage/'
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
