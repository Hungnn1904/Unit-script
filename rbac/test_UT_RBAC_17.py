
from django.test import TestCase, Client
from apps.accounts.models import User

class TestUT_RBAC_17(TestCase):
    def test_UT_RBAC_17(self):
        # Student GET another student's attendance → 403
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
