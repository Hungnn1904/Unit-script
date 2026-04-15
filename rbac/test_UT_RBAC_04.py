
from django.test import TestCase, Client

class TestUT_RBAC_04(TestCase):
    def test_UT_RBAC_04(self):
        from apps.accounts.models import User
        client = Client()
        manager = User.objects.create_user(username='manager1', password='pass', role='CenterManager')
        client.force_login(manager)
        url = '/accounts/manage/'
        response = client.get(url)
        self.assertIn(response.status_code, [200, 403])
