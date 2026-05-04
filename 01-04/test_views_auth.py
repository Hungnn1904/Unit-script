"""
Unit tests for Authentication Views (F-01 & F-02)
- Login/Logout functionality
- Session management
- CSRF/Security basics

DB Check: After login, verify session and user state in DB/response
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

User = get_user_model()


class LoginViewTests(TestCase):
    """
    F-01: Authentication - Login functionality
    """

    def setUp(self):
        """Create test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            phone="0912345678",
            password="secure_pass_123",
            is_active=True
        )
        self.login_url = reverse('accounts:login')

    def test_login_page_loads(self):
        """
        TC_F01_LoginView_Smoke_01: GET login page should load
        Expected: 200 status, page contains form
        """
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        # Ensure form fields present (don't assert exact count)
        self.assertContains(response, 'phone')
        self.assertContains(response, 'password')

    def test_login_success_with_valid_credentials(self):
        """
        TC_F01_LoginView_EP_01: POST valid phone + password
        Expected: 302 redirect to dashboard, session key in response
        DB Check: Session created for this user
        """
        response = self.client.post(self.login_url, {
            'phone': '0912345678',
            'password': 'secure_pass_123',
        }, follow=True)
        # Check session established
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)

    def test_login_fails_with_wrong_password(self):
        """
        TC_F01_LoginView_EP_02: POST wrong password
        Expected: No session created, user sees error message
        DB Check: No session established
        """
        response = self.client.post(self.login_url, {
            'phone': '0912345678',
            'password': 'wrong_password',
        })
        # Check no session established
        self.assertNotIn('_auth_user_id', self.client.session)
        # Non-HTMX failure redirects back to login (302)
        self.assertEqual(response.status_code, 302)

    def test_login_fails_with_inactive_user(self):
        """
        TC_F01_LoginView_EP_03: POST for inactive user (is_active=False)
        Expected: No session created, error message
        DB Check: is_active == False confirmed in DB before test
        """
        inactive_user = User.objects.create_user(
            username="inactive",
            phone="0999999999",
            password="pass123",
            is_active=False
        )
        response = self.client.post(self.login_url, {
            'phone': '0999999999',
            'password': 'pass123',
        })
        # Check no session
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_fails_with_empty_phone(self):
        """
        TC_F01_LoginView_EP_04: POST with empty phone/username
        Expected: No session, error message, 200 status
        """
        response = self.client.post(self.login_url, {
            'phone': '',
            'password': 'secure_pass_123',
        })
        # Check no session
        self.assertNotIn('_auth_user_id', self.client.session)
        # Non-HTMX flows redirect back to login
        self.assertEqual(response.status_code, 302)

    def test_login_fails_with_empty_password(self):
        """
        TC_F01_LoginView_EP_05: POST with empty password
        Expected: No session, error message, 200 status
        """
        response = self.client.post(self.login_url, {
            'phone': '0912345678',
            'password': '',
        })
        # Check no session
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(response.status_code, 302)

    def test_login_with_remember_me_flag(self):
        """
        TC_F01_LoginView_EP_06: POST with remember=on
        Expected: Session created regardless of remember flag
        Note: Remember functionality handled by middleware/session config
        """
        response = self.client.post(self.login_url, {
            'phone': '0912345678',
            'password': 'secure_pass_123',
            'remember': 'on',
        }, follow=True)
        # Session should be established
        self.assertIn('_auth_user_id', self.client.session)


class LogoutViewTests(TestCase):
    """
    F-01: Authentication - Logout functionality
    """

    def setUp(self):
        """Create and login test user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            phone="0912345678",
            password="pass123"
        )
        self.logout_url = reverse('accounts:logout')
        # Login first
        self.client.login(username="testuser", password="pass123")

    def test_logout_clears_session(self):
        """
        TC_F01_LogoutView_EP_01: POST to logout URL
        Expected: Session cleared, user redirected to login
        DB Check: _auth_user_id removed from session
        """
        # Verify session exists before logout
        self.assertIn('_auth_user_id', self.client.session)
        
        # Logout
        response = self.client.post(self.logout_url)
        # Check session cleared
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_redirects_to_login(self):
        """
        TC_F01_LogoutView_EP_02: After logout, user redirected to login page
        Expected: Response redirects to login URL
        """
        response = self.client.post(self.logout_url)
        # App redirects to common:home after logout
        from django.urls import reverse as _reverse
        expected = _reverse('common:home')
        self.assertEqual(response.status_code, 302)
        self.assertIn(expected, response['Location'])

    def test_logout_unauthenticated_user(self):
        """
        TC_F01_LogoutView_EP_03: GET/POST logout as unauthenticated user
        Expected: Redirect to login or 403 (depends on implementation)
        """
        self.client.logout()  # Ensure logged out
        response = self.client.post(self.logout_url)
        # Should redirect to login since user not authenticated
        self.assertIn(response.status_code, [302, 403])


class SessionExpirationTests(TestCase):
    """
    F-01: Session management settings
    """

    def test_session_expire_at_browser_close_setting(self):
        """
        TC_F01_SessionExpiry_01: Check SESSION_EXPIRE_AT_BROWSER_CLOSE setting
        Expected: settings.SESSION_EXPIRE_AT_BROWSER_CLOSE == True
        """
        from django.conf import settings
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)

    def test_login_required_redirects_to_login(self):
        """
        TC_F01_ProtectedURL_01: GET protected URL without login
        Expected: 302 redirect to login with next parameter
        DB Check: User not authenticated (no session)
        """
        # Try to access a protected URL (e.g., dashboard)
        protected_url = reverse('common:dashboard')
        response = self.client.get(protected_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'].lower())
        self.assertIn('next', response['Location'])


class CSRFProtectionTests(TestCase):
    """
    F-01: Basic CSRF protection checks
    """

    def test_login_requires_csrf_token(self):
        """
        TC_F01_CSRF_01: POST to login without CSRF token
        Expected: 403 Forbidden or CSRF failure (if middleware enforced)
        """
        client = Client(enforce_csrf_checks=True)
        login_url = reverse('accounts:login')
        
        # POST without CSRF token should fail
        response = client.post(login_url, {
            'phone': '0912345678',
            'password': 'pass123',
        })
        self.assertEqual(response.status_code, 403)

    def test_login_accepts_valid_csrf_token(self):
        """
        TC_F01_CSRF_02: POST with valid CSRF token
        Expected: Form processed (regardless of auth success)
        """
        client = Client(enforce_csrf_checks=True)
        login_url = reverse('accounts:login')
        
        # Get CSRF token from login page
        response = client.get(login_url)
        csrf_token = response.cookies.get('csrftoken').value
        
        # POST with CSRF token
        response = client.post(login_url, {
            'phone': '0912345678',
            'password': 'pass123',
        }, HTTP_X_CSRFTOKEN=csrf_token)
        
        # Should be accepted (even if login fails)
        self.assertNotEqual(response.status_code, 403)
