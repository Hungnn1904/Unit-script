from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.centers.models import Center
import json

User = get_user_model()

class UserManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a superuser to access management views
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPassword123'
        )
        self.client.login(username='admin', password='AdminPassword123')
        
        # Create a center
        self.center = Center.objects.create(name='EDS-HN')
        
        # Create necessary groups
        self.teacher_group = Group.objects.create(name='Teacher')
        self.student_group = Group.objects.create(name='Student')
        
    def test_ut_um_01_create_user_success(self):
        """Create user – all valid required fields → success"""
        url = reverse('accounts:add_user')
        data = {
            'first_name': 'Le Van',
            'last_name': 'B',
            'email': 'levanb@example.com',
            'phone': '0911222333',
            'password1': 'Pass@1234',
            'password2': 'Pass@1234',
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '123456789012',
            'address': 'Hanoi',
            'center': self.center.id,
            'groups': [self.teacher_group.id],
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200) # The view returns 200 for HTMX success
        
        # Check if user is created
        user = User.objects.get(email='levanb@example.com')
        self.assertEqual(user.first_name, 'Le Van')
        self.assertEqual(user.last_name, 'B')
        self.assertEqual(user.phone, '0911222333')
        self.assertEqual(user.role, 'Teacher')
        self.assertEqual(user.center, self.center)
        self.assertTrue(user.user_code.startswith('EDS'))

    def test_ut_um_02_duplicate_phone(self):
        """Create user – duplicate phone → currently accepted (known bug)"""
        # First user
        User.objects.create(username='user1', phone='0901234567')
        
        url = reverse('accounts:add_user')
        data = {
            'first_name': 'User',
            'last_name': 'Two',
            'email': 'user2@example.com',
            'phone': '0901234567',
            'password1': 'Pass@1234',
            'password2': 'Pass@1234',
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '123456789013',
            'address': 'Hanoi',
            'center': self.center.id,
            'groups': [self.teacher_group.id],
            'is_active': True
        }
        response = self.client.post(url, data)
        # Based on the code, it should succeed because there's no unique check for phone
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(phone='0901234567').count() >= 2)

    def test_ut_um_03_missing_phone_rejected(self):
        """Create user – missing required field (phone) for Teacher → rejected"""
        url = reverse('accounts:add_user')
        data = {
            'first_name': 'No',
            'last_name': 'Phone',
            'email': 'nophone@example.com',
            'phone': '',
            'password1': 'Pass@1234',
            'password2': 'Pass@1234',
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '123456789014',
            'address': 'Hanoi',
            'groups': [self.teacher_group.id],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Số điện thoại là bắt buộc cho vai trò này.', response.content.decode('utf-8'))

    def test_ut_um_04_phone_format_not_checked(self):
        """Create user – phone not starting with 0 → accepted (current implementation doesn't check)"""
        url = reverse('accounts:add_user')
        data = {
            'first_name': 'Bad',
            'last_name': 'Phone',
            'email': 'badphone@example.com',
            'phone': '1901234567',
            'password1': 'Pass@1234',
            'password2': 'Pass@1234',
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '123456789015',
            'address': 'Hanoi',
            'groups': [self.teacher_group.id],
        }
        response = self.client.post(url, data)
        # The code doesn't have phone validation yet
        self.assertEqual(response.status_code, 200)

    def test_ut_um_05_deactivate_user(self):
        """Deactivate active user → is_active=False"""
        target_user = User.objects.create(username='target', is_active=True)
        url = reverse('accounts:delete_users')
        data = {
            'single_user_id': target_user.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        target_user.refresh_from_db()
        self.assertFalse(target_user.is_active)

    def test_ut_um_06_reactivate_user(self):
        """Reactivate inactive user → is_active=True"""
        target_user = User.objects.create(username='inactive', is_active=False)
        url = reverse('accounts:edit_user', kwargs={'user_id': target_user.id})
        # Need to provide all required fields for AdminUserUpdateForm
        data = {
            'first_name': 'Inactive',
            'last_name': 'User',
            'email': 'inactive@example.com',
            'phone': '0912345678',
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '123456789016',
            'address': 'Hanoi',
            'groups': [self.teacher_group.id],
            'is_active': True # This reactivates the user
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        target_user.refresh_from_db()
        self.assertTrue(target_user.is_active)

    def test_ut_um_07_delete_user_actually_deactivates(self):
        """Delete user → currently only deactivates (known implementation)"""
        target_user = User.objects.create(username='todelete', is_active=True)
        url = reverse('accounts:delete_users')
        data = {'single_user_id': target_user.id}
        self.client.post(url, data)
        
        # Check if still in DB
        self.assertTrue(User.objects.filter(id=target_user.id).exists())
        target_user.refresh_from_db()
        self.assertFalse(target_user.is_active)

    def test_ut_um_08_assign_role_update_profile(self):
        """Assign role 'Teacher' (via groups) → user.role updated"""
        target_user = User.objects.create(
            username='roleupdate', 
            role='STUDENT',
            first_name='Role',
            last_name='Update',
            email='role@example.com',
            dob='1990-01-01',
            gender='M',
            national_id='123456789017',
            address='Hanoi'
        )
        target_user.groups.add(self.student_group)
        
        url = reverse('accounts:edit_user', kwargs={'user_id': target_user.id})
        data = {
            'first_name': 'Role',
            'last_name': 'Update',
            'email': 'role@example.com',
            'phone': '0912345678',
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '123456789017',
            'address': 'Hanoi',
            'groups': [self.teacher_group.id], # Change from Student to Teacher
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        target_user.refresh_from_db()
        self.assertEqual(target_user.role, 'Teacher')

    def test_ut_um_09_invalid_national_id(self):
        """Create user – invalid national_id (too short) → rejected"""
        url = reverse('accounts:add_user')
        data = {
            'first_name': 'Short',
            'last_name': 'Nid',
            'email': 'shortnid@example.com',
            'phone': '0911222334',
            'password1': 'Pass@1234',
            'password2': 'Pass@1234',
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '12345', # Too short
            'address': 'Hanoi',
            'groups': [self.teacher_group.id],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('CCCD phải gồm đúng 12 chữ số.', response.content.decode('utf-8'))

    def test_ut_um_10_duplicate_national_id(self):
        """Create user – duplicate national_id → rejected"""
        User.objects.create(username='nid1', national_id='123456789012')
        
        url = reverse('accounts:add_user')
        data = {
            'first_name': 'Dup',
            'last_name': 'Nid',
            'email': 'dupnid@example.com',
            'phone': '0911222335',
            'password1': 'Pass@1234',
            'password2': 'Pass@1234',
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '123456789012', # Duplicate
            'address': 'Hanoi',
            'groups': [self.teacher_group.id],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('CCCD đã tồn tại trong hệ thống.', response.content.decode('utf-8'))

    def test_ut_um_11_password_mismatch(self):
        """Create user – password mismatch → rejected"""
        url = reverse('accounts:add_user')
        data = {
            'first_name': 'Pass',
            'last_name': 'Mismatch',
            'email': 'mismatch@example.com',
            'phone': '0911222336',
            'password1': 'Pass@1234',
            'password2': 'Pass@5678', # Different
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '123456789018',
            'address': 'Hanoi',
            'groups': [self.teacher_group.id],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Mật khẩu và xác nhận mật khẩu không trùng.', response.content.decode('utf-8'))

    def test_ut_um_12_create_student_no_phone_allowed(self):
        """Create student – no phone number → allowed"""
        url = reverse('accounts:add_user')
        data = {
            'first_name': 'Student',
            'last_name': 'NoPhone',
            'email': 'stnophone@example.com',
            'phone': '',
            'password1': 'Pass@1234',
            'password2': 'Pass@1234',
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '123456789019',
            'address': 'Hanoi',
            'groups': [self.student_group.id],
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        user = User.objects.get(email='stnophone@example.com')
        self.assertEqual(user.phone, '')
        self.assertEqual(user.role, 'Student')

    def test_ut_um_13_update_user_role_prefix(self):
        """Update user role Teacher -> Student → verify role and user_code prefix change (if applicable)"""
        target_user = User.objects.create(
            username='roleprefix', 
            role='TEACHER',
            user_code='EDS0001',
            first_name='Prefix',
            last_name='Change',
            email='prefix@example.com',
            dob='1990-01-01',
            gender='M',
            national_id='123456789020',
            address='Hanoi'
        )
        target_user.groups.add(self.teacher_group)

        url = reverse('accounts:edit_user', kwargs={'user_id': target_user.id})
        data = {
            'first_name': 'Prefix',
            'last_name': 'Change',
            'email': 'prefix@example.com',
            'phone': '0912345678',
            'gender': 'M',
            'dob': '1990-01-01',
            'national_id': '123456789020',
            'address': 'Hanoi',
            'groups': [self.student_group.id], # Change to Student
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        target_user.refresh_from_db()
        self.assertEqual(target_user.role, 'Student')
        # In current AdminUserUpdateForm.save(), user_code is NOT regenerated.
        self.assertEqual(target_user.user_code, 'EDS0001')

    def test_ut_um_14_unauthorized_access(self):
        """Regular user – access management → rejected (403)"""
        self.client.logout()
        regular_user = User.objects.create_user(username='regular', password='password123')
        self.client.login(username='regular', password='password123')
        
        url = reverse('accounts:manage_accounts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
