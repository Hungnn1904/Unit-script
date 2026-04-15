import pytest

from .forms import LoginForm


@pytest.mark.django_db
class TestLoginFormValidatePhone:
    @pytest.fixture(autouse=True)
    def setup_user(self, django_user_model):
        self.user = django_user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            phone="0123456789",
            password="TestPass123",
            is_active=True,
        )

    def test_clean_phone_empty(self):
        form = LoginForm(
            data={
                "phone": "",
                "password": "TestPass123",
                "remember": False,
            }
        )
        assert not form.is_valid()
        assert "Vui lòng nhập số điện thoại." in form.errors["phone"]

    def test_validate_phone_invalid_characters(self):
        form = LoginForm(
            data={
                "phone": "01234abcde",
                "password": "TestPass123",
                "remember": False,
            }
        )
        assert not form.is_valid()
        assert "Số điện thoại chỉ được chứa chữ số." in form.errors["__all__"]

    def test_validate_phone_too_short(self):
        form = LoginForm(
            data={
                "phone": "123",
                "password": "TestPass123",
                "remember": False,
            }
        )
        assert not form.is_valid()
        assert "Số điện thoại phải có từ 10 đến 15 chữ số." in form.errors["__all__"]

    def test_validate_phone_too_long(self):
        form = LoginForm(
            data={
                "phone": "01234567890123456",
                "password": "TestPass123",
                "remember": False,
            }
        )
        assert not form.is_valid()
        assert "Số điện thoại phải có từ 10 đến 15 chữ số." in form.errors["__all__"]