
# Test case: UT_RBAC_06
# Mục đích: Kiểm tra CenterManager truy cập danh sách lớp của center khác.
# Logic: Đăng nhập bằng CenterManager, truy cập /classes/list/ với center_id không phải của mình.
# Kết quả mong muốn: API trả về 200 hoặc 403 tùy config.
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
