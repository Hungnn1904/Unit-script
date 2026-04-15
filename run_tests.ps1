# run_tests.ps1
# Chạy pytest cho từng file test riêng biệt và hiển thị kết quả chi tiết.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

Write-Host 'Running pytest for individual test files...' -ForegroundColor Cyan

# Danh sách các test files
$testFiles = @(
    'apps/accounts/test_login_view.py',
    'apps/accounts/test_login_form_clean.py',
    'apps/accounts/test_login_form_validate_phone.py',
    'apps/accounts/test_logout_view.py',
    'apps/accounts/test_password_reset_views.py',
    'apps/accounts/test_change_password_view.py',
    'apps/accounts/test_forgot_password_form.py',
    'apps/accounts/test_user_password_change_form.py',
    'apps/accounts/test_user_set_password_form.py',
    'apps/accounts/test_password_reset_services.py'
)

foreach ($testFile in $testFiles) {
    Write-Host "`nRunning tests in: $testFile" -ForegroundColor Yellow
    python -m pytest $testFile -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Tests failed in: $testFile" -ForegroundColor Red
    } else {
        Write-Host "Tests passed in: $testFile" -ForegroundColor Green
    }
}

Write-Host "`nAll test files completed." -ForegroundColor Cyan
