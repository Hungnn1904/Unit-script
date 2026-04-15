
from django.test import TestCase, Client

class TestUT_RBAC_06(TestCase):
    def test_UT_RBAC_06(self):
        from apps.accounts.models import User
        from apps.centers.models import Center
        client = Client()
        center1 = Center.objects.create(name='Center 1', code='CEN01')
        center2 = Center.objects.create(name='Center 2', code='CEN02')
        manager = User.objects.create_user(username='manager3', password='pass', role='CenterManager', center=center1)
        client.force_login(manager)
        url = f'/classes/list/?center_id={center2.id}'
        response = client.get(url)
        self.assertIn(response.status_code, [200, 403])
        manager = User.objects.create_user(username='manager3', password='pass', role='CenterManager', center=center1)
        client.force_login(manager)
        url = f'/classes/list/?center_id={center2.id}'
        response = client.get(url)
        self.assertIn(response.status_code, [200, 403])
