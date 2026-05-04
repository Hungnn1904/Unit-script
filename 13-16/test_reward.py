"""
Merged rewards tests from:
- test_rewards_combined.py
- test_views.py
- test_signals.py

Tests are ordered by TC ID and grouped by feature area.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from unittest.mock import patch

from apps.attendance.models import Attendance
from apps.rewards import services
from apps.rewards.models import (
    PointAccount,
    RedemptionRequest,
    RedemptionStatus,
    RewardItem,
    RewardTransaction,
    SessionPointEvent,
    SessionPointEventType,
)
from apps.students.models import StudentProduct

User = get_user_model()


@pytest.fixture(autouse=True)
def rollback_db(db):
    """Roll back every test transaction to prevent DB state leaks between tests."""
    with transaction.atomic():
        yield
        transaction.set_rollback(True)


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        password="admin123",
        email="admin@test.com",
    )


@pytest.fixture
def auth_client(client, admin_user):
    client.force_login(admin_user)
    return client


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        username="student1",
        password="student123",
        email="student@test.com",
        role="STUDENT",
    )


@pytest.fixture
def approver_user(db):
    return User.objects.create_user(
        username="approver",
        password="approver123",
        email="approver@test.com",
        role="STAFF",
    )


@pytest.fixture
def reward_item(db):
    from apps.rewards.models import RewardItem

    return RewardItem.objects.create(
        name="Gaming Laptop",
        cost=500,
        description="High-end laptop",
        stock=5,
        is_active=True,
    )


@pytest.fixture
def reward_item_low_stock(db):
    from apps.rewards.models import RewardItem

    return RewardItem.objects.create(
        name="Tablet",
        cost=300,
        description="Mid-range tablet",
        stock=1,
        is_active=True,
    )


@pytest.fixture
def reward_item_inactive(db):
    from apps.rewards.models import RewardItem

    return RewardItem.objects.create(
        name="Discontinued Item",
        cost=200,
        description="Old item",
        stock=10,
        is_active=False,
    )


@pytest.fixture
def point_account_student(db, student_user):
    from apps.rewards.models import PointAccount

    return PointAccount.objects.create(
        student=student_user,
        balance=1000,
    )


@pytest.fixture
def point_account_no_balance(db):
    from apps.rewards.models import PointAccount

    student = User.objects.create_user(
        username="poor_student",
        password="poor123",
        email="poor@test.com",
        role="STUDENT",
    )
    return PointAccount.objects.create(
        student=student,
        balance=0,
    )


@pytest.fixture
def center(db):
    from apps.centers.models import Center

    return Center.objects.create(name="Test Center")


@pytest.fixture
def class_session(db, center):
    from apps.curriculum.models import Subject
    from apps.classes.models import Class
    from apps.class_sessions.models import ClassSession
    from datetime import date, time

    subject = Subject.objects.create(name="Test Subject")
    klass = Class.objects.create(
        code="TST-01",
        name="Test Class",
        center=center,
        subject=subject,
        status="ONGOING",
    )
    return ClassSession.objects.create(
        klass=klass,
        index=1,
        date=date.today(),
        start_time=time(9, 0),
        end_time=time(10, 30),
        status="DONE",
    )


@pytest.mark.django_db
# TC_RWD_01: create point account for a new student
def test_ut_rwd_01_point_account_create_for_new_student(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    student = User.objects.create_user(
        username="new_student",
        email="new@test.com",
        role="STUDENT",
    )

    account = PointAccount.get_or_create_for_student(student)

    assert account is not None
    assert account.student == student
    assert account.balance == 0


@pytest.mark.django_db
# TC_RWD_02: get or create returns existing account
def test_ut_rwd_02_point_account_get_existing(point_account_student):
    account1 = PointAccount.get_or_create_for_student(point_account_student.student)
    account2 = PointAccount.get_or_create_for_student(point_account_student.student)

    assert account1.id == account2.id
    assert account1.balance == 1000
    assert account2.balance == 1000


@pytest.mark.django_db
# TC_RWD_03: adjust balance increases by delta
def test_ut_rwd_03_adjust_balance_add_points(point_account_student):
    initial_balance = point_account_student.balance
    point_account_student.adjust_balance(100)

    point_account_student.refresh_from_db()
    assert point_account_student.balance == initial_balance + 100


@pytest.mark.django_db
# TC_RWD_04: multiple adjustments accumulate correctly
def test_ut_rwd_04_adjust_balance_atomic_integrity(point_account_student):
    initial = point_account_student.balance
    deltas = [10, 20, 30, 40]

    for delta in deltas:
        point_account_student.adjust_balance(delta)

    point_account_student.refresh_from_db()
    expected = initial + sum(deltas)
    assert point_account_student.balance == expected


@pytest.mark.django_db
# TC_RWD_05: create reward item with valid fields
def test_ut_rwd_05_create_reward_item_with_valid_data(db):
    item = RewardItem.objects.create(
        name="Phone",
        cost=400,
        description="Latest smartphone",
        stock=3,
        is_active=True,
    )

    assert item.name == "Phone"
    assert item.cost == 400
    assert item.stock == 3
    assert item.is_active is True


@pytest.mark.django_db
# TC_RWD_06: browse catalog returns only active items
def test_ut_rwd_06_browse_reward_catalog(db):
    RewardItem.objects.create(name="Item A", cost=100, stock=5, is_active=True)
    RewardItem.objects.create(name="Item B", cost=200, stock=0, is_active=True)
    RewardItem.objects.create(name="Item C", cost=300, stock=5, is_active=False)

    active_items = RewardItem.objects.filter(is_active=True)

    assert active_items.count() == 2
    assert all(item.is_active for item in active_items)
    assert not any(item.name == "Item C" for item in active_items)


@pytest.mark.django_db
# TC_RWD_07: deactivating item sets is_active False
def test_ut_rwd_07_deactivate_reward_item(reward_item):
    reward_item.is_active = False
    reward_item.save()

    reward_item.refresh_from_db()
    assert reward_item.is_active is False


@pytest.mark.django_db
# TC_RWD_08: award points with valid positive delta
def test_ut_rwd_08_award_points_valid_delta(student_user):
    PointAccount.objects.create(student=student_user, balance=100)

    txn = services.award_points(
        student=student_user,
        delta=50,
        reason="Bonus points",
    )

    assert txn is not None
    assert txn.delta == 50
    assert txn.reason == "Bonus points"

    student_user.point_account.refresh_from_db()
    assert student_user.point_account.balance == 150


@pytest.mark.django_db
# TC_RWD_09: awarding zero or negative delta raises ValidationError
def test_ut_rwd_09_award_points_invalid_delta_raises_error(student_user):
    PointAccount.objects.create(student=student_user, balance=100)
    count_before = RewardTransaction.objects.count()

    with pytest.raises(ValidationError):
        services.award_points(student=student_user, delta=0, reason="Invalid")

    with pytest.raises(ValidationError):
        services.award_points(student=student_user, delta=-10, reason="Invalid")

    assert RewardTransaction.objects.count() == count_before


@pytest.mark.django_db
# TC_RWD_10: award_points creates a RewardTransaction linked to item
def test_ut_rwd_10_award_points_creates_transaction_record(student_user, reward_item):
    PointAccount.objects.create(student=student_user, balance=0)

    txn = services.award_points(
        student=student_user,
        delta=25,
        reason="Attendance",
        item=reward_item,
    )

    assert txn.item == reward_item
    assert txn.reason == "Attendance"

    txn.refresh_from_db()
    assert txn.id is not None


@pytest.mark.django_db
# TC_RWD_11: submit redemption when student has sufficient points and stock
def test_ut_rwd_11_submit_redemption_sufficient_points_stock(
    student_user, reward_item
):
    PointAccount.objects.create(student=student_user, balance=1000)
    item_stock_before = reward_item.stock

    req = services.submit_redemption_request(
        student=student_user,
        item=reward_item,
        quantity=2,
        note="Want this",
    )

    assert req is not None
    assert req.status == RedemptionStatus.PENDING
    assert req.quantity == 2
    assert req.cost_snapshot == reward_item.cost
    assert req.total_cost == reward_item.cost * 2
    reward_item.refresh_from_db()
    assert reward_item.stock == item_stock_before


@pytest.mark.django_db
# TC_RWD_12: submitting redemption with insufficient points raises error
def test_ut_rwd_12_submit_redemption_insufficient_points(
    point_account_no_balance, reward_item
):
    with pytest.raises(ValidationError, match="chưa đủ điểm"):
        services.submit_redemption_request(
            student=point_account_no_balance.student,
            item=reward_item,
            quantity=1,
        )


@pytest.mark.django_db
# TC_RWD_13: submitting redemption when stock < quantity raises error
def test_ut_rwd_13_submit_redemption_insufficient_stock(student_user, reward_item):
    PointAccount.objects.create(student=student_user, balance=10000)
    reward_item.stock = 1

    with pytest.raises(ValidationError, match="Không đủ tồn kho"):
        services.submit_redemption_request(
            student=student_user,
            item=reward_item,
            quantity=2,
        )


@pytest.mark.django_db
# TC_RWD_14: submitting redemption for inactive item raises error
def test_ut_rwd_14_submit_redemption_inactive_item(student_user, reward_item_inactive):
    PointAccount.objects.create(student=student_user, balance=10000)

    with pytest.raises(ValidationError, match="tạm khóa"):
        services.submit_redemption_request(
            student=student_user,
            item=reward_item_inactive,
            quantity=1,
        )


@pytest.mark.django_db
# TC_RWD_15: invalid quantities (0, negative) raise ValidationError
def test_ut_rwd_15_submit_redemption_invalid_quantity(student_user, reward_item):
    PointAccount.objects.create(student=student_user, balance=10000)

    with pytest.raises(ValidationError):
        services.submit_redemption_request(
            student=student_user,
            item=reward_item,
            quantity=0,
        )

    with pytest.raises(ValidationError):
        services.submit_redemption_request(
            student=student_user,
            item=reward_item,
            quantity=-1,
        )


@pytest.mark.django_db
# TC_RWD_16: pending -> approved deducts stock and points
def test_ut_rwd_16_transition_pending_to_approved(student_user, reward_item, approver_user):
    PointAccount.objects.create(student=student_user, balance=1000)
    req = services.submit_redemption_request(
        student=student_user, item=reward_item, quantity=1
    )
    stock_before = reward_item.stock
    balance_before = student_user.point_account.balance

    req = services.approve_redemption_request(
        req=req,
        approver=approver_user,
        note="OK",
    )

    assert req.status == RedemptionStatus.APPROVED
    assert req.approved_by == approver_user

    reward_item.refresh_from_db()
    student_user.point_account.refresh_from_db()
    assert reward_item.stock == stock_before - 1
    assert student_user.point_account.balance == balance_before - req.total_cost


@pytest.mark.django_db
# TC_RWD_17: approved -> fulfilled sets status fulfilled
def test_ut_rwd_17_transition_approved_to_fulfilled(
    student_user, reward_item, approver_user
):
    PointAccount.objects.create(student=student_user, balance=1000)
    req = services.submit_redemption_request(
        student=student_user, item=reward_item, quantity=1
    )
    req = services.approve_redemption_request(req=req, approver=approver_user)

    req = services.fulfill_redemption_request(req=req, approver=approver_user, note="Delivered")

    assert req.status == RedemptionStatus.FULFILLED


@pytest.mark.django_db
# TC_RWD_18: pending -> rejected leaves stock and balance unchanged
def test_ut_rwd_18_transition_pending_to_rejected_no_refund(
    student_user, reward_item, approver_user
):
    PointAccount.objects.create(student=student_user, balance=1000)
    req = services.submit_redemption_request(
        student=student_user, item=reward_item, quantity=1
    )
    balance_before = student_user.point_account.balance
    stock_before = reward_item.stock

    req = services.reject_redemption_request(req=req, approver=approver_user)

    assert req.status == RedemptionStatus.REJECTED
    student_user.point_account.refresh_from_db()
    reward_item.refresh_from_db()
    assert student_user.point_account.balance == balance_before
    assert reward_item.stock == stock_before


@pytest.mark.django_db
# TC_RWD_20: pending -> cancelled by student leaves stock and balance
def test_ut_rwd_20_transition_pending_to_cancelled_no_refund(
    student_user, reward_item, approver_user
):
    PointAccount.objects.create(student=student_user, balance=1000)
    req = services.submit_redemption_request(
        student=student_user, item=reward_item, quantity=1
    )
    balance_before = student_user.point_account.balance
    stock_before = reward_item.stock

    req = services.cancel_redemption_request(req=req, actor=student_user)

    assert req.status == RedemptionStatus.CANCELLED
    student_user.point_account.refresh_from_db()
    reward_item.refresh_from_db()
    assert student_user.point_account.balance == balance_before
    assert reward_item.stock == stock_before


@pytest.mark.django_db
# TC_RWD_22: cannot reject a fulfilled request (ValidationError)
def test_ut_rwd_22_invalid_transition_fulfilled_to_rejected(
    student_user, reward_item, approver_user
):
    PointAccount.objects.create(student=student_user, balance=1000)
    req = services.submit_redemption_request(
        student=student_user, item=reward_item, quantity=1
    )
    req = services.approve_redemption_request(req=req, approver=approver_user)
    req = services.fulfill_redemption_request(req=req, approver=approver_user)

    with pytest.raises(ValidationError):
        services.reject_redemption_request(req=req, approver=approver_user)

    req.refresh_from_db()
    assert req.status == RedemptionStatus.FULFILLED


@pytest.mark.django_db
# TC_RWD_23: approve is atomic: stock decreased and points deducted once
def test_ut_rwd_23_atomic_approve_stock_and_point_deduction(
    student_user, reward_item, approver_user
):
    PointAccount.objects.create(student=student_user, balance=1000)
    req = services.submit_redemption_request(
        student=student_user, item=reward_item, quantity=2
    )
    total_cost = req.total_cost
    stock_before = reward_item.stock
    balance_before = student_user.point_account.balance

    req = services.approve_redemption_request(req=req, approver=approver_user)

    reward_item.refresh_from_db()
    student_user.point_account.refresh_from_db()
    txns = RewardTransaction.objects.filter(redemption=req)

    assert reward_item.stock == stock_before - 2
    assert student_user.point_account.balance == balance_before - total_cost
    assert txns.count() == 1
    assert txns.first().delta == -total_cost


@pytest.mark.django_db
# TC_RWD_26: award session point creates transaction and updates balance
def test_ut_rwd_26_award_session_point_valid_event(student_user):
    PointAccount.objects.create(student=student_user, balance=0)

    txn = services.award_points(student=student_user, delta=10, reason="Reward")

    assert txn is not None
    student_user.point_account.refresh_from_db()
    assert student_user.point_account.balance == 10


@pytest.mark.django_db
# TC_RWD_27: multiple award_points calls accumulate correctly
def test_ut_rwd_27_award_points_multiple_times(student_user):
    PointAccount.objects.create(student=student_user, balance=100)
    services.award_points(student=student_user, delta=10, reason="r1")
    services.award_points(student=student_user, delta=20, reason="r2")
    services.award_points(student=student_user, delta=30, reason="r3")

    student_user.point_account.refresh_from_db()
    assert student_user.point_account.balance == 160


@pytest.mark.django_db
# TC_RWD_28: award_points recorded in RewardTransaction history
def test_ut_rwd_28_point_transactions_recorded_in_history(student_user, reward_item):
    PointAccount.objects.create(student=student_user, balance=0)
    services.award_points(student=student_user, delta=50, reason="audit", item=reward_item)

    txns = RewardTransaction.objects.filter(student=student_user)
    assert txns.exists()
    assert txns.first().reason == "audit"


@pytest.mark.django_db
# TC_RWD_19: account summary paginates and preserves query params
def test_account_summary_paginates_and_preserves_query_params(client, student_user, reward_item):
    client.force_login(student_user)
    PointAccount.objects.create(student=student_user, balance=200)

    RewardTransaction.objects.create(student=student_user, delta=10, reason="A", item=reward_item)
    RewardTransaction.objects.create(student=student_user, delta=20, reason="B", item=reward_item)
    RewardTransaction.objects.create(student=student_user, delta=30, reason="C", item=reward_item)

    RedemptionRequest.objects.create(
        student=student_user,
        item=reward_item,
        quantity=1,
        cost_snapshot=reward_item.cost,
    )

    response = client.get(reverse("rewards:account_summary") + "?page=2&per_page=2&foo=bar")

    assert response.status_code == 200
    assert response.context["transactions_total"] == 3
    assert response.context["page_obj"].number == 2
    assert response.context["per_page"] == 2
    assert any(param["name"] == "foo" for param in response.context["preserved_query_params"])


@pytest.mark.django_db
# TC_RWD_21: catalog shows active in-stock items and creates account
def test_catalog_shows_active_in_stock_items_and_creates_account(
    client, student_user, reward_item, reward_item_low_stock, reward_item_inactive
):
    client.force_login(student_user)
    RewardItem.objects.create(name="Zero Stock", cost=100, stock=0, is_active=True)

    response = client.get(reverse("rewards:catalog"))

    assert response.status_code == 200
    assert response.context["account"].student == student_user
    items = list(response.context["items"])
    assert len(items) == 2
    assert all(item.is_active and item.stock > 0 for item in items)


@pytest.mark.django_db
# TC_RWD_24: submit request valid and invalid paths
def test_submit_request_valid_and_invalid_paths(client, student_user, reward_item, point_account_student):
    client.force_login(student_user)

    valid_response = client.post(
        reverse("rewards:submit_request"),
        {"item": reward_item.pk, "quantity": 1, "note": "Need this"},
    )
    assert valid_response.status_code == 302
    assert RedemptionRequest.objects.filter(student=student_user, item=reward_item).count() == 1

    invalid_response = client.post(
        reverse("rewards:submit_request"),
        {"quantity": 1, "note": "Missing item"},
    )
    assert invalid_response.status_code == 302


@pytest.mark.django_db
# TC_RWD_25: award points GET and POST paths
def test_award_points_get_and_post_paths(client, admin_user, student_user, class_session):
    client.force_login(admin_user)
    get_response = client.get(reverse("rewards:award_points"))
    assert get_response.status_code == 200

    post_no_session = client.post(
        reverse("rewards:award_points"),
        {"student": student_user.pk, "delta": 10, "reason": "Manual award"},
    )
    assert post_no_session.status_code == 302
    assert PointAccount.objects.get(student=student_user).balance == 10

    post_with_session = client.post(
        reverse("rewards:award_points"),
        {"student": student_user.pk, "session": class_session.pk, "delta": 5, "reason": "Session award"},
    )
    assert post_with_session.status_code == 302
    assert RewardTransaction.objects.filter(student=student_user, session=class_session).exists()


@pytest.mark.django_db
# TC_RWD_29: manage items GET and HTMX POST paths
def test_manage_items_get_and_htmx_post_paths(client, admin_user):
    perm = Permission.objects.get(codename="change_rewarditem")
    admin_user.user_permissions.add(perm)
    client.force_login(admin_user)

    get_response = client.get(reverse("rewards:manage_items"))
    assert get_response.status_code == 200

    valid_response = client.post(
        reverse("rewards:manage_items"),
        {
            "name": "Gift Card",
            "description": "E-voucher",
            "cost": 100,
            "stock": 3,
            "is_active": "on",
        },
        HTTP_HX_REQUEST="true",
    )
    assert valid_response.status_code == 204
    assert RewardItem.objects.filter(name="Gift Card").exists()

    invalid_response = client.post(
        reverse("rewards:manage_items"),
        {"description": "Missing name", "cost": 100, "stock": 3, "is_active": "on"},
        HTTP_HX_REQUEST="true",
    )
    assert invalid_response.status_code == 422


@pytest.mark.django_db
# TC_RWD_30: manage requests and action views
def test_manage_requests_and_action_views(client, admin_user, student_user, reward_item):
    perm = Permission.objects.get(codename="change_redemptionrequest")
    admin_user.user_permissions.add(perm)
    client.force_login(admin_user)
    PointAccount.objects.create(student=student_user, balance=1000)

    approve_req = RedemptionRequest.objects.create(
        student=student_user,
        item=reward_item,
        quantity=1,
        cost_snapshot=reward_item.cost,
    )
    reject_req = RedemptionRequest.objects.create(
        student=student_user,
        item=reward_item,
        quantity=1,
        cost_snapshot=reward_item.cost,
    )
    fulfill_req = RedemptionRequest.objects.create(
        student=student_user,
        item=reward_item,
        quantity=1,
        cost_snapshot=reward_item.cost,
    )
    cancel_req = RedemptionRequest.objects.create(
        student=student_user,
        item=reward_item,
        quantity=1,
        cost_snapshot=reward_item.cost,
    )

    assert client.get(reverse("rewards:manage_requests")).status_code == 200
    assert client.post(reverse("rewards:approve_request", args=[approve_req.pk]), {"note": "ok"}).status_code == 302
    assert client.post(reverse("rewards:reject_request", args=[reject_req.pk]), {"note": "reject"}).status_code == 302
    assert client.post(reverse("rewards:approve_request", args=[fulfill_req.pk]), {"note": "ok"}).status_code == 302
    assert client.post(reverse("rewards:fulfill_request", args=[fulfill_req.pk]), {"note": "done"}).status_code == 302
    assert client.post(reverse("rewards:cancel_request", args=[cancel_req.pk]), {"note": "cancel"}).status_code == 302


@pytest.mark.django_db
# TC_RWD_31: attendance signal awards point when present
def test_attendance_signal_awards_point_when_present(class_session, student_user):
    attendance = Attendance.objects.create(session=class_session, student=student_user, status="P")

    assert Attendance.objects.filter(pk=attendance.pk).exists()
    assert RewardTransaction.objects.filter(student=student_user, session=class_session, delta=1).exists()
    assert SessionPointEvent.objects.filter(
        student=student_user,
        session=class_session,
        event_type=SessionPointEventType.ATTENDANCE,
    ).exists()


@pytest.mark.django_db
# TC_RWD_32: attendance signal ignores non-present
def test_attendance_signal_ignores_non_present(student_user, class_session):
    txn_count_before = RewardTransaction.objects.filter(student=student_user, session=class_session).count()
    event_count_before = SessionPointEvent.objects.filter(student=student_user, session=class_session).count()
    
    attendance = Attendance.objects.create(session=class_session, student=student_user, status="A")
    
    assert attendance.pk is not None
    txn_count_after = RewardTransaction.objects.filter(student=student_user, session=class_session).count()
    event_count_after = SessionPointEvent.objects.filter(student=student_user, session=class_session).count()
    assert txn_count_after == txn_count_before
    assert event_count_after == event_count_before


@pytest.mark.django_db
# TC_RWD_33: attendance signal creates point on present attendance
def test_attendance_signal_creates_point_on_present(class_session, student_user):
    PointAccount.objects.create(student=student_user, balance=0)
    
    attendance = Attendance.objects.create(session=class_session, student=student_user, status="P")
    
    assert attendance.pk is not None
    assert RewardTransaction.objects.filter(student=student_user, session=class_session, delta=1).exists()
    assert SessionPointEvent.objects.filter(
        student=student_user,
        session=class_session,
        event_type=SessionPointEventType.ATTENDANCE,
    ).exists()


@pytest.mark.django_db
# TC_RWD_34: student product signal awards point on create
def test_student_product_signal_awards_point_on_create(class_session, student_user):
    product = StudentProduct.objects.create(
        session=class_session,
        student=student_user,
        title="Demo product",
        description="Created from test",
    )

    assert product.pk is not None
    assert RewardTransaction.objects.filter(student=student_user, session=class_session, delta=1).exists()
    assert SessionPointEvent.objects.filter(
        student=student_user,
        session=class_session,
        event_type=SessionPointEventType.PRODUCT,
    ).exists()


@pytest.mark.django_db
# TC_RWD_35: student product signal ignores updates
def test_student_product_signal_ignores_updates(class_session, student_user):
    PointAccount.objects.create(student=student_user, balance=0)
    
    product = StudentProduct.objects.create(
        session=class_session,
        student=student_user,
        title="Existing product",
        description="Initial",
    )
    
    txn_count_after_create = RewardTransaction.objects.filter(student=student_user, session=class_session).count()
    event_count_after_create = SessionPointEvent.objects.filter(student=student_user, session=class_session).count()
    
    product.description = "Updated"
    product.save()
    
    txn_count_after_update = RewardTransaction.objects.filter(student=student_user, session=class_session).count()
    event_count_after_update = SessionPointEvent.objects.filter(student=student_user, session=class_session).count()
    
    assert txn_count_after_update == txn_count_after_create
    assert event_count_after_update == event_count_after_create
