import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestLogoutView:
    @pytest.fixture(autouse=True)
    def setup_user(self, client, django_user_model):
        self.user = django_user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            phone="0123456789",
            password="TestPass123",
            is_active=True,
        )
        client.login(username="testuser", password="TestPass123")

    def test_logout_success(self, client):
        response = client.post(reverse("accounts:logout"))
        assert response.status_code == 302  # Redirect after logout
        assert not response.wsgi_request.user.is_authenticated

    def test_logout_get_request(self, client):
        response = client.get(reverse("accounts:logout"))
        assert response.status_code == 302
        assert not response.wsgi_request.user.is_authenticated