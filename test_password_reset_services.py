import pytest
from django.core import mail
from django.test import RequestFactory

from .services import build_password_reset_link, send_password_reset_email


@pytest.mark.django_db
class TestPasswordResetServices:
    @pytest.fixture(autouse=True)
    def setup_user(self, django_user_model):
        self.user = django_user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            phone="0123456789",
            password="TestPass123",
            is_active=True,
        )

    def test_build_password_reset_link(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.META["HTTP_HOST"] = "example.com"
        link = build_password_reset_link(self.user, request)
        assert "password_reset_confirm" in link
        assert "example.com" in link

    def test_send_password_reset_email_success(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.META["HTTP_HOST"] = "example.com"
        result = send_password_reset_email(self.user, request)
        assert result is True
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert self.user.email in email.to
        assert "Hướng dẫn đặt lại mật khẩu" in email.subject

    def test_send_password_reset_email_no_email(self, django_user_model):
        user_no_email = django_user_model.objects.create_user(
            username="noemail",
            phone="0987654321",
            password="TestPass123",
            is_active=True,
        )
        factory = RequestFactory()
        request = factory.get("/")
        result = send_password_reset_email(user_no_email, request)
        assert result is False
        assert len(mail.outbox) == 0