import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification


@pytest.fixture(autouse=True)
def rollback(db):
    """Ensure DB changes are rolled back after each test.

    Reason: tests in this suite create notifications and users; rollback
    guarantees isolation and avoids leaving persistent rows across tests.
    """
    from django.db import transaction

    with transaction.atomic():
        yield
        # Mark the transaction to be rolled back to keep test DB clean
        transaction.set_rollback(True)


@pytest.mark.django_db
def test_system_notification_delivery():
    User = get_user_model()
    user = User.objects.create_user(username="notify_user", password="pass")

    # Deliver a notification (system creates a Notification row)
    n = Notification.objects.create(user=user, title="Welcome", body="Hello!")

    assert n.pk is not None
    assert n.user_id == user.id
    assert n.title == "Welcome"
    assert not n.is_read


@pytest.mark.django_db
def test_mark_as_read():
    User = get_user_model()
    user = User.objects.create_user(username="reader", password="pass")
    n = Notification.objects.create(user=user, title="Later", body="Read me")

    # Mark as read and ensure persisted
    n.is_read = True
    n.save(update_fields=["is_read"])

    n2 = Notification.objects.get(pk=n.pk)
    assert n2.is_read is True


@pytest.mark.django_db
def test_read_status_tracking_counts():
    User = get_user_model()
    user = User.objects.create_user(username="tracker", password="pass")

    # Create mix of read/unread notifications
    Notification.objects.create(user=user, title="One", body="1")
    Notification.objects.create(user=user, title="Two", body="2")
    r = Notification.objects.create(user=user, title="Three", body="3")
    r.is_read = True
    r.save(update_fields=["is_read"])

    unread_qs = Notification.objects.filter(user=user, is_read=False)
    assert unread_qs.count() == 2

    # Mark one unread as read and assert counts update
    first = unread_qs.first()
    first.is_read = True
    first.save(update_fields=["is_read"])

    assert Notification.objects.filter(user=user, is_read=False).count() == 1


@pytest.mark.django_db
def test_notification_string_representation():
    User = get_user_model()
    user = User.objects.create_user(username="repr_user", password="pass")

    notification = Notification.objects.create(user=user, title="System Alert", body="Body")

    assert str(notification) == "repr_user: System Alert"
