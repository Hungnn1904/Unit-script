
# Test case: UT_RBAC_17
# Mục đích: Kiểm tra học sinh này truy cập lịch sử điểm danh của học sinh khác.
# Logic: Đăng nhập bằng student1, truy cập lịch sử của student2.
# Kết quả mong muốn: API trả về 403 hoặc 404.
from django.test import TestCase, Client
from apps.accounts.models import User

class TestUT_RBAC_17(TestCase):
    def test_UT_RBAC_17(self):
        client = Client()
        student1 = User.objects.create_user(username='student17a', password='pass', role='Student')
        student2 = User.objects.create_user(username='student17b', password='pass', role='Student')
        client.force_login(student1)
        url = f'/attendance/history/{student2.id}/'
        response = client.get(url)
        self.assertEqual(response.status_code, 403)
        client = Client()
        student1 = User.objects.create_user(username='student17a', password='pass', role='Student')
        student2 = User.objects.create_user(username='student17b', password='pass', role='Student')
        client.force_login(student1)
        url = f'/attendance/history/{student2.id}/'
        response = client.get(url)
        self.assertIn(response.status_code, [403, 404])
