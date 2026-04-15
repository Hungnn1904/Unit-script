import pytest
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator


@pytest.mark.django_db
class TestPasswordResetViews:
    @pytest.fixture(autouse=True)
    def setup_user(self, django_user_model):
        self.user = django_user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            phone="0123456789",
            password="TestPass123",
            is_active=True,
        )

    def test_password_reset_request_success(self, client):
        response = client.post(
            reverse("accounts:password_reset"),
            {"identifier": "test@example.com"},
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert "Hướng dẫn đặt lại mật khẩu" in email.subject

    def test_password_reset_request_unknown_user(self, client):
        response = client.post(
            reverse("accounts:password_reset"),
            {"identifier": "unknown@example.com"},
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 0

    def test_password_reset_done_get(self, client):
        response = client.get(reverse("accounts:password_reset_done"))
        assert response.status_code == 200

    def test_password_reset_confirm_valid_token(self, client):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse("accounts:password_reset_confirm", kwargs={"uidb64": uid, "token": token})
        response = client.post(
            url,
            {"new_password1": "NewPass123", "new_password2": "NewPass123"},
        )
        assert response.status_code == 302

    def test_password_reset_confirm_invalid_token(self, client):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = reverse("accounts:password_reset_confirm", kwargs={"uidb64": uid, "token": "invalid"})
        response = client.post(
            url,
            {"new_password1": "NewPass123", "new_password2": "NewPass123"},
        )
        assert response.status_code == 200  # Should show form again

    def test_password_reset_complete_get(self, client):
        response = client.get(reverse("accounts:password_reset_complete"))
        assert response.status_code == 200