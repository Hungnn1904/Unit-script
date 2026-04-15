
from django.test import TestCase, Client
from apps.accounts.models import User

class TestUT_RBAC_14(TestCase):
    def test_UT_RBAC_14(self):
        # Student can submit learning product → HTTP 302
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
        # Có thể là 302 (redirect) hoặc 200 tuỳ hệ thống
        self.assertIn(response.status_code, [200, 302])
