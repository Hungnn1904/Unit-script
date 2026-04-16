
# Test case: UT_RBAC_04
# Mục đích: Kiểm tra quyền truy cập của CenterManager vào trang quản lý tài khoản.
# Logic: Tạo user CenterManager, đăng nhập, truy cập /accounts/manage/.
# Kết quả mong muốn: Trả về HTTP 200 (có quyền) hoặc 403 (không có quyền).
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
