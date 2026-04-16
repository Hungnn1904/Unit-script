
# Test case: UT_RBAC_01
# Mục đích: Kiểm tra quyền truy cập của admin vào trang quản lý tài khoản.
# Logic: Tạo user admin, đăng nhập, truy cập /accounts/manage/.
# Kết quả mong muốn: Trả về HTTP 200 (PASS).
from django.test import TestCase, Client

class TestUT_RBAC_01(TestCase):
    def test_UT_RBAC_01(self):
        # Admin accesses /accounts/manage/ → HTTP 200 (system test: PASS)
        from apps.accounts.models import User
        client = Client()
        admin = User.objects.create_superuser(username='admin', password='pass', role='Admin', email='admin@example.com')
        client.force_login(admin)
        url = '/accounts/manage/'
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
