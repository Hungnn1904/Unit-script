import pytest

from .forms import UserSetPasswordForm


@pytest.mark.django_db
class TestUserSetPasswordForm:
    @pytest.fixture(autouse=True)
    def setup_user(self, django_user_model):
        self.user = django_user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            phone="0123456789",
            password="OldPass123",
            is_active=True,
        )

    def test_form_valid(self):
        form = UserSetPasswordForm(
            user=self.user,
            data={
                "new_password1": "NewPass123",
                "new_password2": "NewPass123",
            },
        )
        assert form.is_valid()

    def test_form_invalid_mismatched_passwords(self):
        form = UserSetPasswordForm(
            user=self.user,
            data={
                "new_password1": "NewPass123",
                "new_password2": "DifferentPass",
            },
        )
        assert not form.is_valid()
        assert "password_mismatch" in str(form.errors)