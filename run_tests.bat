@echo off
REM run_tests.bat
REM Chạy pytest cho từng file test riêng biệt và hiển thị kết quả chi tiết.
cd /d %~dp0

echo Running pytest for individual test files...

REM Danh sách các test files
set "testFiles[0]=apps/accounts/test_login_view.py"
set "testFiles[1]=apps/accounts/test_login_form_clean.py"
set "testFiles[2]=apps/accounts/test_login_form_validate_phone.py"
set "testFiles[3]=apps/accounts/test_logout_view.py"
set "testFiles[4]=apps/accounts/test_password_reset_views.py"
set "testFiles[5]=apps/accounts/test_change_password_view.py"
set "testFiles[6]=apps/accounts/test_forgot_password_form.py"
set "testFiles[7]=apps/accounts/test_user_password_change_form.py"
set "testFiles[8]=apps/accounts/test_user_set_password_form.py"
set "testFiles[9]=apps/accounts/test_password_reset_services.py"

for /L %%i in (0,1,9) do (
    echo.
    echo Running tests in: !testFiles[%%i]!
    python -m pytest !testFiles[%%i]! -v
    if errorlevel 1 (
        echo Tests failed in: !testFiles[%%i]!
    ) else (
        echo Tests passed in: !testFiles[%%i]!
    )
)

echo.
echo All test files completed.
