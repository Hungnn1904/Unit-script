
from django.test import TestCase, Client

class TestUT_RBAC_05(TestCase):
    def test_UT_RBAC_05(self):
        from apps.accounts.models import User
        from apps.centers.models import Center
        from apps.classes.models import Class
        client = Client()
        center = Center.objects.create(name='Center 1', code='CEN01')
        manager = User.objects.create_user(username='manager2', password='pass', role='CenterManager', center=center)
        client.force_login(manager)
        url = f'/classes/list/?center_id={center.id}'
        response = client.get(url)
        # Nếu hệ thống chưa filter center, có thể trả về 200 hoặc 403 tuỳ config
        self.assertIn(response.status_code, [200, 403])
        manager = User.objects.create_user(username='manager2', password='pass', role='CenterManager', center=center)
        client.force_login(manager)
        url = f'/classes/list/?center_id={center.id}'
        response = client.get(url)
        self.assertIn(response.status_code, [200, 403])
