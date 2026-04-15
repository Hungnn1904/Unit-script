import pytest

from .forms import LoginForm


@pytest.mark.django_db
class TestLoginFormClean:
    @pytest.fixture(autouse=True)
    def setup_user(self, django_user_model):
        self.user = django_user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            phone="0123456789",
            password="TestPass123",
            is_active=True,
        )

    def test_form_valid(self):
        form = LoginForm(
            data={
                "phone": "0123456789",
                "password": "TestPass123",
                "remember": False,
            }
        )
        assert form.is_valid()
        assert form.cleaned_data["user"] == self.user

    def test_form_invalid_wrong_password(self):
        form = LoginForm(
            data={
                "phone": "0123456789",
                "password": "WrongPass",
                "remember": False,
            }
        )
        assert not form.is_valid()
        assert "Mật khẩu không đúng." in form.errors["__all__"]

    def test_form_invalid_user_not_found(self):
        form = LoginForm(
            data={
                "phone": "0999999999",
                "password": "TestPass123",
                "remember": False,
            }
        )
        assert not form.is_valid()
        assert "Không tìm thấy tài khoản với số điện thoại này." in form.errors["__all__"]