
 
# Test case: UT_RBAC_16
# Mục đích: Kiểm tra học sinh truy cập lịch sử điểm danh của chính mình.
# Logic: Đăng nhập bằng student, truy cập /attendance/history/{student.id}/.
# Kết quả mong muốn: API trả về 200 hoặc 403.
from django.test import TestCase, Client
from apps.accounts.models import User

class TestUT_RBAC_16(TestCase):
    def test_UT_RBAC_16(self):
        client = Client()
        student = User.objects.create_user(username='student16', password='pass', role='Student')
        client.force_login(student)
        url = f'/attendance/history/{student.id}/'
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        client = Client()
        student = User.objects.create_user(username='student16', password='pass', role='Student')
        client.force_login(student)
        url = f'/attendance/history/{student.id}/'
        response = client.get(url)
        self.assertIn(response.status_code, [200, 403])
