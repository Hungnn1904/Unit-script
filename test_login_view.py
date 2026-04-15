import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestLoginView:
    @pytest.fixture(autouse=True)
    def setup_user(self, django_user_model):
        self.user = django_user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            phone="0123456789",
            password="TestPass123",
            is_active=True,
        )

    def test_login_get_request(self, client):
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 200
        assert "login" in response.template_name[0]

    def test_login_success_with_phone(self, client):
        response = client.post(
            reverse("accounts:login"),
            {
                "phone": "0123456789",
                "password": "TestPass123",
                "remember": "off",
            },
        )
        assert response.status_code == 302
        assert response.wsgi_request.user.is_authenticated

    def test_login_success_with_email(self, client):
        response = client.post(
            reverse("accounts:login"),
            {
                "phone": "test@example.com",
                "password": "TestPass123",
                "remember": "off",
            },
        )
        assert response.status_code == 302
        assert response.wsgi_request.user.is_authenticated

    def test_login_failure_wrong_password(self, client):
        response = client.post(
            reverse("accounts:login"),
            {
                "phone": "0123456789",
                "password": "WrongPass",
                "remember": "off",
            },
        )
        assert response.status_code == 302
        assert not response.wsgi_request.user.is_authenticated

    def test_login_failure_user_not_found(self, client):
        response = client.post(
            reverse("accounts:login"),
            {
                "phone": "0999999999",
                "password": "TestPass123",
                "remember": "off",
            },
        )
        assert response.status_code == 302
        assert not response.wsgi_request.user.is_authenticated

    def test_login_failure_empty_phone(self, client):
        response = client.post(
            reverse("accounts:login"),
            {
                "phone": "",
                "password": "TestPass123",
                "remember": "off",
            },
        )
        assert response.status_code == 302
        assert not response.wsgi_request.user.is_authenticated

    def test_login_with_remember_me(self, client):
        response = client.post(
            reverse("accounts:login"),
            {
                "phone": "0123456789",
                "password": "TestPass123",
                "remember": "on",
            },
        )
        assert response.status_code == 302
        assert response.wsgi_request.user.is_authenticated