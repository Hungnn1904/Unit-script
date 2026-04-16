
 
# Test case: UT_RBAC_14
# Mục đích: Kiểm tra học sinh gửi sản phẩm (product) lên hệ thống.
# Logic: Đăng nhập bằng student, gửi POST sản phẩm.
# Kết quả mong muốn: API trả về 302 hoặc 200.
from django.test import TestCase, Client
from apps.accounts.models import User

class TestUT_RBAC_14(TestCase):
    def test_UT_RBAC_14(self):
        client = Client()
        student = User.objects.create_user(username='student14', password='pass', role='Student')
        client.force_login(student)
        url = '/products/submit/'
        data = {'product_id': 1, 'content': 'My work'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 302)
        client = Client()
        student = User.objects.create_user(username='student14', password='pass', role='Student')
        client.force_login(student)
        url = '/products/submit/'
        data = {'product_id': 1, 'content': 'My work'}
        response = client.post(url, data)
        self.assertIn(response.status_code, [200, 302])
