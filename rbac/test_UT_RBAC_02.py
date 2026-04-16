
# Test case: UT_RBAC_02
# Mục đích: Kiểm tra quyền truy cập của admin vào trang quản lý lớp học.
# Logic: Tạo user admin, đăng nhập, truy cập /classes/manage/.
# Kết quả mong muốn: Trả về HTTP 200 (PASS).
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
