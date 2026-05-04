from unittest.mock import Mock, patch

from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.signals import (
    _delete_field_file,
    user_avatar_delete_on_change,
    user_avatar_delete_on_model_delete,
)


class AccountSignalsTests(TestCase):
    def test_delete_field_file_swallows_storage_errors(self):
        file_field = Mock()
        file_field.name = "avatars/old.jpg"
        file_field.delete.side_effect = Exception("storage error")

        _delete_field_file(file_field)

        file_field.delete.assert_called_once_with(save=False)

    def test_delete_field_file_ignores_missing_name(self):
        file_field = Mock()
        file_field.name = ""

        _delete_field_file(file_field)

        file_field.delete.assert_not_called()

    @patch("apps.accounts.signals._delete_field_file")
    def test_model_delete_signal_calls_delete_helper(self, delete_mock):
        avatar = Mock()
        avatar.name = "avatars/old.jpg"
        instance = Mock(spec=User)
        instance.avatar = avatar

        user_avatar_delete_on_model_delete(sender=User, instance=instance)

        delete_mock.assert_called_once_with(avatar)

    @patch("apps.accounts.signals._delete_field_file")
    @patch("apps.accounts.signals.User.objects.get")
    def test_avatar_change_signal_deletes_old_file_when_avatar_changes(self, get_mock, delete_mock):
        old_avatar = Mock()
        old_avatar.name = "avatars/old.jpg"
        old_user = Mock()
        old_user.avatar = old_avatar
        get_mock.return_value = old_user

        new_avatar = Mock()
        new_avatar.name = "avatars/new.jpg"
        instance = Mock(spec=User)
        instance.pk = 1
        instance.avatar = new_avatar

        user_avatar_delete_on_change(sender=User, instance=instance)

        delete_mock.assert_called_once_with(old_avatar)

    @patch("apps.accounts.signals._delete_field_file")
    def test_avatar_change_signal_noop_without_pk(self, delete_mock):
        instance = Mock(spec=User)
        instance.pk = None
        instance.avatar = None

        user_avatar_delete_on_change(sender=User, instance=instance)

        delete_mock.assert_not_called()

    @patch("apps.accounts.signals._delete_field_file")
    @patch("apps.accounts.signals.User.objects.get", side_effect=User.DoesNotExist)
    def test_avatar_change_signal_noop_when_old_user_missing(self, get_mock, delete_mock):
        instance = Mock(spec=User)
        instance.pk = 999999
        instance.avatar = None

        user_avatar_delete_on_change(sender=User, instance=instance)

        get_mock.assert_called_once()
        delete_mock.assert_not_called()
