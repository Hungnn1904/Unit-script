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
