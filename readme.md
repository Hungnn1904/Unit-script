## Testing

### Tổng Quan
Dự án có 2 hệ thống test:
1. **Django Tests** (unittest-based) - file `apps/accounts/tests.py`
2. **Pytest Tests** (pytest-based) - các file `apps/accounts/test_*.py`


### Cài Đặt File
```bash
pytest.ini, run_tests.bat, run_tests.ps1 đưa vào folder gốc dự án
các file test python đưa vào trong thư mục apps\accounts

```

### Cài Đặt Dependencies Test
```bash
pip install -r requirements.txt
```

### Chạy Django Tests
```bash
# Chạy tất cả Django tests
python manage.py test

# Chạy tests cho apps/accounts
python manage.py test apps.accounts.tests --verbosity=2 --keepdb
```

### Chạy Pytest Tests
```bash
# Chạy tất cả pytest tests
python -m pytest

# Chạy tests cho apps/accounts
python -m pytest apps/accounts/ --verbosity=2

# Chạy test file cụ thể
python -m pytest apps/accounts/test_login_view.py -v
```

### Script Chạy Test Tự Động
Dự án cung cấp script để chạy tất cả test một cách tự động:

#### Windows PowerShell
```powershell
.\run_tests.ps1
```

#### Windows Command Prompt
```cmd
run_tests.bat
```

### Các File Test Pytest
- `test_login_view.py` - Test login view (7 test cases)
- `test_login_form_clean.py` - Test LoginForm.clean (3 test cases)
- `test_login_form_validate_phone.py` - Test LoginForm.validate_phone (4 test cases)
- `test_logout_view.py` - Test logout view (2 test cases)
- `test_password_reset_views.py` - Test password reset views (6 test cases)
- `test_change_password_view.py` - Test change password view (4 test cases)
- `test_forgot_password_form.py` - Test ForgotPasswordForm (4 test cases)
- `test_user_password_change_form.py` - Test UserPasswordChangeForm (3 test cases)
- `test_user_set_password_form.py` - Test UserSetPasswordForm (2 test cases)
- `test_password_reset_services.py` - Test password reset services (3 test cases)

**Tổng cộng: 38 test cases** cho toàn bộ authentication system.

### Cấu Hình Pytest
- File `pytest.ini` chứa cấu hình Django settings và options
- Sử dụng `@pytest.mark.django_db` cho database tests
- Tích hợp với Django test client và fixtures



Các Method/Function Được Test:

1. Login Authentication:
- login_view (function) - Xử lý POST/GET login.
- LoginForm.clean (method) - Validation tổng thể form login.
- LoginForm.validate_phone (method) - Validation riêng phone number.

2. Logout Authentication:
- logout_view (function) - Đăng xuất user.
3. Password Reset Flow:
- password_reset_request_view (function) - Gửi yêu cầu reset.
- password_reset_done_view (function) - Hiển thị sau gửi yêu cầu.
- password_reset_confirm_view (function) - Xác nhận reset từ link.
- password_reset_complete_view (function) - Hoàn thành reset.
- ForgotPasswordForm (class) - Form quên password.
- build_password_reset_link (function) - Tạo link reset.
- send_password_reset_email (function) - Gửi email reset.
4. Change Password:
- change_password_view (function) - Thay đổi password khi login.
- UserPasswordChangeForm (class) - Form đổi password.
- UserSetPasswordForm (class) - Form đặt password mới.
Tổng cộng: 38 test cases cho 13 method/function chính liên quan đến authentication.

Các Method/Function Không Được Test (và Tại Sao):
1. User Management (Không liên quan trực tiếp đến authentication):
- AdminUserCreateForm.save - Tạo user mới (không phải login/logout).
- AdminUserUpdateForm.save - Cập nhật user (không phải auth).
- UserProfileUpdateForm - Cập nhật profile (không phải auth).
- detect_prefix_from_groups - Helper cho user code (không phải auth).
- UserCodeCounter.next_code - Sinh user code (không phải auth).
2. Admin/Staff Functions:
- SimpleGroupForm - Quản lý groups (không phải user auth).
- ImportUserForm - Import users (không phải login flow).
3. Utility/Helper Functions:
- _password_reset_rate_key - Rate limiting key (đã test gián tiếp qua views).
- _is_password_reset_rate_limited - Kiểm tra rate limit (đã test gián tiếp).
- _increment_password_reset_rate - Tăng counter (đã test gián tiếp).
- _password_reset_success_response - Response helper (đã test qua views).
4. Model Methods:
- User.set_password - Đã test gián tiếp qua forms/views.
- User.check_password - Đã test gián tiếp qua login.
- User.preferred_email - Đã test gián tiếp qua email sending.
5. Other Views:
- Các view admin, reports, etc. - Không liên quan đến user authentication.