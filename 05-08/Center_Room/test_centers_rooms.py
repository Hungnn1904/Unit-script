import json
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.exceptions import PermissionDenied

from apps.centers.models import Center, Room
from apps.centers.forms import CenterForm, RoomForm
from apps.centers.filters import CenterFilter
from apps.common.utils.forms import form_errors_as_text
from apps.centers.views import _filter_rooms_queryset, center_delete_view, room_delete_view
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestCenterModels:
    """Kiểm tra logic của model Center"""
    
    def test_tc01_center_str_representation(self):
        """TC_01: Kiểm tra hàm __str__ của model Center"""
        center = Center.objects.create(name="Trung tâm STEAM PTIT", code="STEAM01")
        assert str(center) == "Trung tâm STEAM PTIT"

    def test_tc02_center_default_is_active(self):
        """TC_02: Kiểm tra giá trị mặc định của trường is_active"""
        center = Center.objects.create(name="Test Center", code="TEST01")
        assert center.is_active is True

    def test_tc03_center_code_uniqueness(self):
        """TC_03: Kiểm tra ràng buộc duy nhất (Unique) của mã trung tâm"""
        Center.objects.create(name="Center 1", code="C01")
        with pytest.raises(IntegrityError):
            Center.objects.create(name="Center 2", code="C01")


@pytest.mark.django_db
class TestRoomModels:
    """Kiểm tra logic của model Room"""

    def test_tc04_room_str_representation(self):
        """TC_04: Kiểm tra hàm __str__ của model Room"""
        center = Center.objects.create(name="PTIT", code="P01")
        room = Room.objects.create(center=center, name="Lab 101")
        assert str(room) == "PTIT - Lab 101"

    def test_tc05_room_uniqueness_per_center(self):
        """TC_05: Kiểm tra ràng buộc Unique Together (center, name) của Room"""
        center1 = Center.objects.create(name="Center 1", code="C1")
        center2 = Center.objects.create(name="Center 2", code="C2")
        
        Room.objects.create(center=center1, name="Room A")
        
        # Cho phép cùng tên ở 2 trung tâm khác nhau
        Room.objects.create(center=center2, name="Room A") 
        
        # Chặn cùng tên ở cùng 1 trung tâm
        with pytest.raises(IntegrityError):
            Room.objects.create(center=center1, name="Room A")


@pytest.mark.django_db
class TestCenterForms:
    """Kiểm tra logic của CenterForm (Validation)"""

    def test_tc06_center_form_valid_data(self):
        """TC_06: Kiểm tra form Center với dữ liệu hợp lệ"""
        data = {
            'name': 'Trung tâm Mới',
            'code': 'NEW01',
            'address': 'Hà Nội',
            'is_active': True
        }
        form = CenterForm(data=data)
        assert form.is_valid()
        # Lưu vào DB và kiểm tra
        center = form.save()
        assert Center.objects.filter(code='NEW01').exists()
        assert center.name == 'Trung tâm Mới'

    def test_tc07_center_form_duplicate_code_validation(self):
        """TC_07: Kiểm tra validation chặn mã trung tâm đã tồn tại"""
        Center.objects.create(name="Existing", code="EXISTING")
        
        # Test trùng mã (case-insensitive)
        data = {'name': 'New', 'code': 'existing'}
        form = CenterForm(data=data)
        
        assert not form.is_valid()
        assert 'code' in form.errors
        assert form.errors['code'][0] == "Mã Trung tâm này đã tồn tại."

    def test_tc08_center_form_update_same_code(self):
        """TC_08: Kiểm tra form khi update chính trung tâm đó (không báo lỗi trùng mã)"""
        center = Center.objects.create(name="Existing", code="EXISTING")
        data = {'name': 'Existing Updated', 'code': 'EXISTING'}
        form = CenterForm(data=data, instance=center)
        assert form.is_valid()
        # Lưu và kiểm tra DB đã cập nhật tên mới chưa
        form.save()
        center.refresh_from_db()
        assert center.name == 'Existing Updated'

    def test_tc17_center_form_clean_code_whitespace(self):
        """TC_17: Kiểm tra clean_code với khoảng trắng (leading/trailing)"""
        # Lưu ý: Django ModelForm mặc định strip whitespace của CharField
        data = {'name': 'Test', 'code': '  NEW_CODE  '}
        form = CenterForm(data=data)
        assert form.is_valid()
        # Code sau khi clean nên được strip (nếu Form/Field cấu hình mặc định)
        assert form.cleaned_data['code'] == 'NEW_CODE'


@pytest.mark.django_db
class TestRoomForms:
    """Kiểm tra logic của RoomForm"""

    def test_tc16_room_form_unique_together_validation(self):
        """TC_16: Kiểm tra validation unique_together (center, name) ở cấp độ Form"""
        center = Center.objects.create(name="PTIT", code="P01")
        Room.objects.create(center=center, name="Room 101")
        
        data = {'center': center.id, 'name': 'Room 101', 'note': ''}
        form = RoomForm(data=data)
        
        # ModelForm sẽ tự động kiểm tra unique_together trong hàm validate_unique()
        assert not form.is_valid()
        assert '__all__' in form.errors or 'name' in form.errors


@pytest.mark.django_db
class TestCenterFilters:
    """Kiểm tra bộ lọc CenterFilter"""

    @pytest.fixture
    def setup_centers(self):
        Center.objects.create(name="Alpha", code="A1", address="Hanoi", is_active=True)
        Center.objects.create(name="Beta", code="B1", address="HCM", is_active=False)

    def test_tc09_filter_by_search_query(self, setup_centers):
        """TC_09: Kiểm tra tính năng tìm kiếm (Search Query)"""
        qs = Center.objects.all()
        
        # Tìm theo tên
        f = CenterFilter({'q': 'Alpha'}, queryset=qs)
        assert f.qs.count() == 1
        
        # Tìm theo mã
        f = CenterFilter({'q': 'B1'}, queryset=qs)
        assert f.qs.count() == 1

        # Tìm theo địa chỉ
        f = CenterFilter({'q': 'Hanoi'}, queryset=qs)
        assert f.qs.count() == 1

    def test_tc10_filter_by_status(self, setup_centers):
        """TC_10: Kiểm tra tính năng lọc theo trạng thái (Status)"""
        qs = Center.objects.all()
        
        # Lọc active
        f = CenterFilter({'status': 'active'}, queryset=qs)
        assert f.qs.count() == 1
        assert f.qs[0].name == "Alpha"

        # Lọc inactive
        f = CenterFilter({'status': 'inactive'}, queryset=qs)
        assert f.qs.count() == 1
        assert f.qs[0].name == "Beta"

    def test_tc15_filter_empty_query(self, setup_centers):
        """TC_15: Kiểm tra filter với chuỗi tìm kiếm rỗng hoặc chỉ có khoảng trắng"""
        qs = Center.objects.all()
        
        f = CenterFilter({'q': '   '}, queryset=qs)
        assert f.qs.count() == qs.count()


class TestUtilityFunctions:
    """Kiểm tra các hàm tiện ích"""

    def test_tc18_form_errors_as_text(self):
        """TC_18: Kiểm tra hàm chuyển đổi lỗi form thành text"""
        class MockForm:
            def __init__(self):
                self.errors = {
                    'name': ['Trường này là bắt buộc.'],
                    'email': ['Email không hợp lệ.']
                }
                self.fields = {
                    'name': MagicMock(label='Tên'),
                    'email': MagicMock(label='Email')
                }
            def non_field_errors(self):
                return ['Lỗi chung.']

        form = MockForm()
        text = form_errors_as_text(form)
        assert "Tên: Trường này là bắt buộc." in text
        assert "Email: Email không hợp lệ." in text
        assert "Lỗi chung." in text


@pytest.mark.django_db
class TestViewHelpers:
    """Kiểm tra các hàm helper trong views"""

    def test_tc19_filter_rooms_queryset_logic(self):
        """TC_19: Kiểm tra logic của hàm _filter_rooms_queryset"""
        center = Center.objects.create(name="Center A", code="CA")
        Room.objects.create(center=center, name="Room 101")
        
        factory = RequestFactory()
        # Mock request GET
        request = factory.get('/rooms/', {'q': '101'})
        
        qs = _filter_rooms_queryset(request)
        
        # Lưu ý: Code gốc đang thiếu 'return qs', nên test này có thể fail (trả về None)
        # Nếu fail, đây là minh chứng cho bug trong code.
        assert qs is not None
        assert qs.filter(name="Room 101").exists()


@pytest.mark.django_db
class TestCenterActions:
    """Kiểm tra các hành động xử lý Trung tâm (Actions)"""

    def test_tc20_center_soft_delete_logic(self):
        """TC_20: Kiểm tra logic 'xóa mềm' (vô hiệu hóa) trung tâm"""
        center = Center.objects.create(name="To Delete", code="DEL", is_active=True)
        
        factory = RequestFactory()
        # Giả lập request POST xóa
        request = factory.post('/centers/delete/', {'center_ids[]': [center.id]})
        
        # Mock user có quyền xóa
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_superuser(username='admin', password='1')
        request.user = user
        
        # Gọi view trực tiếp
        response = center_delete_view(request)
        
        assert response.status_code == 200
        center.refresh_from_db()
        assert center.is_active is False


@pytest.mark.django_db
class TestAccessControl:
    """Kiểm tra phân quyền truy cập"""

    def test_tc21_center_create_permission_denied(self):
        """TC_21: Kiểm tra chặn truy cập khi không có quyền add_center"""
        from apps.centers.views import center_create_view
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.create_user(username='staff', password='1')
        factory = RequestFactory()
        request = factory.get('/centers/create/')
        request.user = user
        
        # Mock session và messages cho middleware nếu cần (ở đây view dùng decorator)
        # Khi dùng permission_required(raise_exception=True), nó sẽ ném lỗi PermissionDenied
        with pytest.raises(PermissionDenied):
            center_create_view(request)
            
    def test_tc21_center_create_permission_granted(self):
        """TC_21: Kiểm tra cho phép truy cập khi có quyền add_center"""
        from apps.centers.views import center_create_view
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.create_user(username='manager', password='1')
        # Gán quyền add_center
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Center)
        permission = Permission.objects.get(content_type=content_type, codename='add_center')
        user.user_permissions.add(permission)
        user = User.objects.get(id=user.id) # Refresh permissions
        
        factory = RequestFactory()
        request = factory.get('/centers/create/')
        request.user = user
        
        response = center_create_view(request)
        assert response.status_code == 200


from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestCenterSignals:
    """Kiểm tra các tín hiệu (Signals)"""

    def test_tc11_avatar_deletion_on_center_delete(self):
        """TC_11: Kiểm tra signal tự động xóa file avatar khi xóa Center"""
        # Truy cập trực tiếp vào storage của field và mock nó
        avatar_field = Center._meta.get_field('avatar')
        original_storage = avatar_field.storage
        
        mock_storage = MagicMock()
        mock_storage.save.return_value = "center_avatars/test.png"
        mock_storage.generate_filename = lambda n: n
        avatar_field.storage = mock_storage
        
        try:
            # Tạo file giả
            avatar = SimpleUploadedFile("test.png", b"content", content_type="image/png")
            center = Center.objects.create(name="Test", code="T1", avatar=avatar)
            
            # Mock hàm delete của file
            with patch.object(center.avatar, 'delete') as mock_avatar_delete:
                center.delete()
                # Kiểm tra signal đã gọi hàm xóa file
                mock_avatar_delete.assert_called_once_with(save=False)
        finally:
            # Khôi phục lại storage sau khi test xong
            avatar_field.storage = original_storage


@pytest.mark.django_db
class TestRoomActions:
    """Kiểm tra các hành động xử lý Phòng học (Actions)"""

    def test_tc22_room_delete_view_single_room(self, admin_user):
        """TC_22: Kiểm tra view xóa một phòng học thành công"""
        center = Center.objects.create(name="Center A", code="CA")
        room1 = Room.objects.create(center=center, name="Room 1")
        room2 = Room.objects.create(center=center, name="Room 2")

        factory = RequestFactory()
        request = factory.post('/rooms/delete/', {'room_ids[]': [room1.id]})
        request.user = admin_user # Gán người dùng đã đăng nhập và có quyền

        response = room_delete_view(request)
        
        assert response.status_code == 200
        assert not Room.objects.filter(id=room1.id).exists()
        assert Room.objects.filter(id=room2.id).exists() # Đảm bảo phòng khác không bị xóa
        
        # Kiểm tra alert message
        response_data = json.loads(response["HX-Trigger"])
        assert "show-sweet-alert" in response_data
        assert response_data["show-sweet-alert"]["icon"] == "success"
        assert f"Đã xóa Phòng học '{room1.center.name} - {room1.name}' thành công." in response_data["show-sweet-alert"]["title"]


    def test_tc23_room_delete_view_multiple_rooms(self, admin_user):
        """TC_23: Kiểm tra view xóa nhiều phòng học thành công"""
        center = Center.objects.create(name="Center B", code="CB")
        room1 = Room.objects.create(center=center, name="Room X")
        room2 = Room.objects.create(center=center, name="Room Y")
        room3 = Room.objects.create(center=center, name="Room Z")

        factory = RequestFactory()
        request = factory.post('/rooms/delete/', {'room_ids[]': [room1.id, room2.id]})
        request.user = admin_user

        response = room_delete_view(request)
        
        assert response.status_code == 200
        assert not Room.objects.filter(id=room1.id).exists()
        assert not Room.objects.filter(id=room2.id).exists()
        assert Room.objects.filter(id=room3.id).exists()
        
        response_data = json.loads(response["HX-Trigger"])
        assert "show-sweet-alert" in response_data
        assert response_data["show-sweet-alert"]["icon"] == "success"
        assert "Đã xóa 2 Phòng học thành công." in response_data["show-sweet-alert"]["title"]
        assert f"'{room1.center.name} - {room1.name}'" in response_data["show-sweet-alert"]["text"]
        assert f"'{room2.center.name} - {room2.name}'" in response_data["show-sweet-alert"]["text"]

    def test_tc24_room_delete_view_no_rooms_selected(self, admin_user):
        """TC_24: Kiểm tra view xóa khi không có phòng học nào được chọn"""
        factory = RequestFactory()
        request = factory.post('/rooms/delete/', {}) # Không gửi room_ids
        request.user = admin_user

        response = room_delete_view(request)
        
        assert response.status_code == 200
        response_data = json.loads(response["HX-Trigger"])
        assert "show-sweet-alert" in response_data
        assert response_data["show-sweet-alert"]["icon"] == "info"
        assert "Không có Phòng học nào được chọn." in response_data["show-sweet-alert"]["title"]

    def test_tc25_room_delete_view_permission_denied(self, user_without_permission):
        """TC_25: Kiểm tra view xóa bị chặn khi người dùng không có quyền"""
        center = Center.objects.create(name="Center C", code="CC")
        room = Room.objects.create(center=center, name="Room PD")

        factory = RequestFactory()
        request = factory.post('/rooms/delete/', {'room_ids[]': [room.id]})
        request.user = user_without_permission # Người dùng không có quyền delete_room

        with pytest.raises(PermissionDenied):
            room_delete_view(request)

    def test_tc26_filter_rooms_queryset_returns_queryset(self):
        """TC_26: Kiểm tra hàm _filter_rooms_queryset trả về queryset (phát hiện bug)"""
        center = Center.objects.create(name="Center F", code="CF")
        Room.objects.create(center=center, name="Room 301")
        
        factory = RequestFactory()
        request = factory.get('/rooms/', {'q': '301'})
        
        qs = _filter_rooms_queryset(request)
        
        assert qs is not None, "BUG: _filter_rooms_queryset không trả về queryset, dẫn đến lỗi NoneType."
        assert hasattr(qs, 'count'), "BUG: _filter_rooms_queryset không trả về một QuerySet hợp lệ."
        assert qs.filter(name="Room 301").exists()

@pytest.fixture
def admin_user():
    """Fixture tạo người dùng admin có tất cả các quyền"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_superuser(username='admin', password='123')
    return user

@pytest.fixture
def user_without_permission():
    """Fixture tạo người dùng không có quyền xóa phòng học"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='noperm', password='123')
    return user
