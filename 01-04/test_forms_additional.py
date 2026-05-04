from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from apps.accounts import forms as acct_forms
from apps.accounts.models import UserCodeCounter

User = get_user_model()


class FormsAdditionalTests(TestCase):
    def test_detect_prefix_from_groups_various(self):
        g_teacher = Group.objects.create(name='Teacher')
        g_parent = Group.objects.create(name='Parent')
        g_student = Group.objects.create(name='Student')
        # teacher -> EDS
        qs = Group.objects.filter(pk=g_teacher.pk)
        self.assertEqual(acct_forms.detect_prefix_from_groups(qs), 'EDS')
        # parent -> PR
        qs = Group.objects.filter(pk=g_parent.pk)
        self.assertEqual(acct_forms.detect_prefix_from_groups(qs), 'PR')
        # student -> ST
        qs = Group.objects.filter(pk=g_student.pk)
        self.assertEqual(acct_forms.detect_prefix_from_groups(qs), 'ST')
        # empty -> US
        self.assertEqual(acct_forms.detect_prefix_from_groups(None), 'US')

    def test_admin_create_form_clean_national_id_duplicate(self):
        # existing user with national id
        User.objects.create_user(username='u1', password='p', national_id='111111111111')
        Group.objects.create(name='Student')
        data = {
            'first_name': 'A', 'last_name': 'B', 'email': 'a@b.com',
            'dob': '1990-01-01', 'gender': 'M', 'national_id': '111111111111',
            'address': 'here', 'groups': [Group.objects.first().id],
            'password1': 'pass1234', 'password2': 'pass1234'
        }
        form = acct_forms.AdminUserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('national_id', form.errors)

    def test_admin_create_form_password_mismatch_and_groups_phone(self):
        # password mismatch
        g = Group.objects.create(name='Teacher')
        data = {
            'first_name': 'A', 'last_name': 'B', 'email': 'c@d.com',
            'dob': '1990-01-01', 'gender': 'M', 'national_id': '',
            'address': 'addr', 'groups': [g.id],
            'password1': 'p1', 'password2': 'p2'
        }
        form = acct_forms.AdminUserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        # password mismatch should be non-field error
        self.assertTrue(any('Mật khẩu' in str(e) or 'không trùng' in str(e) for e in form.non_field_errors()))
        # missing phone for non-student should add phone error
        data['password2'] = 'p1'
        form2 = acct_forms.AdminUserCreateForm(data=data)
        self.assertFalse(form2.is_valid())
        self.assertIn('phone', form2.errors)

    def test_admin_create_form_save_creates_user_and_usercode(self):
        # student role doesn't require phone
        g = Group.objects.create(name='Student')
        data = {
            'first_name': 'First', 'last_name': 'Last', 'email': 'st@example.com',
            'dob': '1990-01-01', 'gender': 'M', 'national_id': '987654321098',
            'address': 'addr', 'groups': [g.id],
            'password1': 'strongpass', 'password2': 'strongpass'
        }
        form = acct_forms.AdminUserCreateForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        user = form.save()
        # username derived from name
        self.assertTrue(user.username.startswith('first-last') or user.username.startswith('user'))
        # user_code created through UserCodeCounter
        self.assertIsNotNone(user.user_code)
        self.assertTrue(UserCodeCounter.objects.filter(prefix='ST').exists())

    def test_simple_group_form_protected_name_change(self):
        # create protected group name
        g = Group.objects.create(name='Admin')
        # instantiate form editing that group but attempt to change name
        form = acct_forms.SimpleGroupForm(instance=g, data={'name': 'AdminChanged', 'permissions': []})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_forgot_password_form_get_user_by_email_and_phone(self):
        u = User.objects.create_user(username='xuser', email='x@example.com', phone='0123456789', password='p')
        form = acct_forms.ForgotPasswordForm(data={'identifier': 'x@example.com'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_user().pk, u.pk)
        form2 = acct_forms.ForgotPasswordForm(data={'identifier': '0123456789'})
        self.assertTrue(form2.is_valid())
        self.assertEqual(form2.get_user().pk, u.pk)

    def test_user_password_change_form_validation(self):
        u = User.objects.create_user(username='chg', password='oldpass')
        # missing new passwords
        form = acct_forms.UserPasswordChangeForm(user=u, data={'old_password': 'oldpass', 'new_password1': '', 'new_password2': ''})
        self.assertFalse(form.is_valid())
        # mismatched new passwords
        form2 = acct_forms.UserPasswordChangeForm(user=u, data={'old_password': 'oldpass', 'new_password1': 'a', 'new_password2': 'b'})
        self.assertFalse(form2.is_valid())

    def test_admin_create_form_save_assigns_user_code_and_role(self):
        student_group = Group.objects.create(name='Student')
        form = acct_forms.AdminUserCreateForm(data={
            'first_name': 'First',
            'last_name': 'Last',
            'email': 'student@example.com',
            'dob': '1990-01-01',
            'gender': 'M',
            'national_id': '123456789012',
            'address': 'Addr',
            'groups': [student_group.id],
            'password1': 'strongpass',
            'password2': 'strongpass',
        })
        self.assertTrue(form.is_valid(), msg=form.errors)

        user = form.save()
        user.refresh_from_db()
        self.assertTrue(user.user_code.startswith('ST'))
        self.assertEqual(user.role, 'Student')
        self.assertTrue(user.check_password('strongpass'))

    def test_admin_update_form_requires_phone_and_checks_duplicate_national_id(self):
        teacher_group = Group.objects.create(name='Teacher')
        other_user = User.objects.create_user(username='other', password='pass123', national_id='222222222222')
        user = User.objects.create_user(username='target', password='pass123', national_id='111111111111')

        form = acct_forms.AdminUserUpdateForm(instance=user, data={
            'first_name': 'Target',
            'last_name': 'User',
            'email': 'target@example.com',
            'dob': '1990-01-01',
            'gender': 'M',
            'national_id': other_user.national_id,
            'address': 'Addr',
            'groups': [teacher_group.id],
            'phone': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('national_id', form.errors)
        self.assertIn('phone', form.errors)

    def test_admin_update_form_save_updates_role_and_phone(self):
        teacher_group = Group.objects.create(name='Teacher')
        user = User.objects.create_user(username='updatable', password='pass123', role='STUDENT')

        form = acct_forms.AdminUserUpdateForm(instance=user, data={
            'first_name': 'Update',
            'last_name': 'Me',
            'email': 'update@example.com',
            'dob': '1990-01-01',
            'gender': 'M',
            'national_id': '333333333333',
            'address': 'Addr',
            'groups': [teacher_group.id],
            'phone': '0912345678',
        })
        self.assertTrue(form.is_valid(), msg=form.errors)

        updated = form.save()
        updated.refresh_from_db()
        self.assertEqual(updated.role, 'Teacher')
        self.assertEqual(updated.phone, '0912345678')

    def test_simple_group_form_blocks_protected_group_rename(self):
        group = Group.objects.create(name='Admin')
        form = acct_forms.SimpleGroupForm(instance=group, data={'name': 'AdminChanged', 'permissions': []})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_simple_group_form_allows_non_protected_group_rename(self):
        group = Group.objects.create(name='CustomGroup')
        form = acct_forms.SimpleGroupForm(instance=group, data={'name': 'RenamedGroup', 'permissions': []})
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_forgot_password_form_finds_user_by_numeric_username(self):
        user = User.objects.create_user(username='1234567890', password='pass123', is_active=True)
        form = acct_forms.ForgotPasswordForm(data={'identifier': '1234567890'})
        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.get_user().pk, user.pk)

    def test_forgot_password_form_rejects_empty_identifier(self):
        form = acct_forms.ForgotPasswordForm(data={'identifier': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('identifier', form.errors)

    def test_user_set_password_form_validates_and_accepts_match(self):
        user = User.objects.create_user(username='resetuser', password='oldpass')
        form = acct_forms.UserSetPasswordForm(user=user, data={'new_password1': 'newpass123', 'new_password2': 'newpass123'})
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_user_profile_update_form_duplicate_national_id(self):
        other_user = User.objects.create_user(username='profile-other', password='pass123', national_id='444444444444')
        user = User.objects.create_user(username='profile-target', password='pass123')
        form = acct_forms.UserProfileUpdateForm(instance=user, data={
            'first_name': 'A',
            'last_name': 'B',
            'email': 'a@example.com',
            'phone': '0912345678',
            'national_id': other_user.national_id,
            'address': 'Addr',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('national_id', form.errors)
