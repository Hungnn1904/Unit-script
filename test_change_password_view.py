import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestChangePasswordView:
    @pytest.fixture(autouse=True)
    def setup_user(self, client, django_user_model):
        self.user = django_user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            phone="0123456789",
            password="OldPass123",
            is_active=True,
        )
        client.login(username="testuser", password="OldPass123")

    def test_change_password_success(self, client):
        response = client.post(
            reverse("accounts:change_password"),
            {
                "old_password": "OldPass123",
                "new_password1": "NewPass123",
                "new_password2": "NewPass123",
            },
        )
        assert response.status_code == 302
        # Verify new password works
        client.logout()
        assert client.login(username="testuser", password="NewPass123")

    def test_change_password_wrong_old_password(self, client):
        response = client.post(
            reverse("accounts:change_password"),
            {
                "old_password": "WrongPass",
                "new_password1": "NewPass123",
                "new_password2": "NewPass123",
            },
        )
        assert response.status_code == 200  # Form error

    def test_change_password_mismatched_new_passwords(self, client):
        response = client.post(
            reverse("accounts:change_password"),
            {
                "old_password": "OldPass123",
                "new_password1": "NewPass123",
                "new_password2": "DifferentPass",
            },
        )
        assert response.status_code == 200  # Form error

    def test_change_password_get_request(self, client):
        response = client.get(reverse("accounts:change_password"))
        assert response.status_code == 200