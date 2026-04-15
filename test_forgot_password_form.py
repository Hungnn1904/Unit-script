import pytest

from .forms import ForgotPasswordForm


@pytest.mark.django_db
class TestForgotPasswordForm:
    @pytest.fixture(autouse=True)
    def setup_user(self, django_user_model):
        self.user = django_user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            phone="0123456789",
            password="TestPass123",
            is_active=True,
        )

    def test_form_valid_with_email(self):
        form = ForgotPasswordForm(data={"identifier": "test@example.com"})
        assert form.is_valid()
        assert form.get_user() == self.user

    def test_form_valid_with_phone(self):
        form = ForgotPasswordForm(data={"identifier": "0123456789"})
        assert form.is_valid()
        assert form.get_user() == self.user

    def test_form_invalid_empty_identifier(self):
        form = ForgotPasswordForm(data={"identifier": ""})
        assert not form.is_valid()
        assert "Vui lòng nhập email hoặc số điện thoại đã đăng ký." in form.errors["identifier"]

    def test_form_invalid_unknown_user(self):
        form = ForgotPasswordForm(data={"identifier": "unknown@example.com"})
        assert not form.is_valid()
        assert form.get_user() is None