# Project Test Documentation

This directory contains unit tests and test tracking for the User Management system.

## Test Tracking
- `testUnit.csv`: Detailed log of unit test cases, techniques used, input data, and current status/findings.

## Unit Tests
- `tests_management.py`: Comprehensive test suite for `apps/accounts` management views and forms.

### Tools Used
- **Django TestCase**: For database isolation and standard test structure.
- **Django Client**: For simulating HTTP requests (POST/GET) to verify views and HTMX responses.
- **Python (venv)**: The project uses a dedicated virtual environment located in `./venv`.

### Test Execution
To run the user management tests, use the following command from the project root:
```bash
./venv/bin/python manage.py test test.tests_management
```

## Detailed Test Analysis (Phân tích các hàm test)

Dưới đây là phân tích chi tiết các hàm kiểm thử trong `tests_management.py`:

### 1. Nhóm Tạo Người Dùng (User Creation)
- **`test_ut_um_01_create_user_success`**: 
    - **Mục tiêu**: Kiểm tra luồng tạo người dùng thành công với đầy đủ dữ liệu hợp lệ.
    - **Phân tích**: Gửi request POST với Center và Group (Teacher). Kiểm tra xem User có được lưu vào DB không, role có đúng là 'Teacher' không và `user_code` có được sinh tự động với prefix 'EDS' không.
- **`test_ut_um_02_duplicate_phone`**:
    - **Mục tiêu**: Kiểm tra xử lý khi trùng số điện thoại.
    - **Phân tích**: Hiện tại hệ thống **chưa chặn** trùng số điện thoại (Bug). Hàm test xác nhận rằng 2 user có thể có cùng số điện thoại.
- **`test_ut_um_03_missing_phone_rejected`**:
    - **Mục tiêu**: Kiểm tra tính bắt buộc của số điện thoại cho vai trò Teacher/Admin.
    - **Phân tích**: Vai trò Teacher yêu cầu phone. Test gửi dữ liệu trống và xác nhận nhận lỗi 400 cùng thông báo lỗi tương ứng.
- **`test_ut_um_12_create_student_no_phone_allowed`**:
    - **Mục tiêu**: Kiểm tra ngoại lệ cho vai trò Student.
    - **Phân tích**: Khác với Teacher, Student không bắt buộc có phone. Test xác nhận tạo Student thành công khi để trống phone.

### 2. Nhóm Trạng Thái & Xóa (State & Deletion)
- **`test_ut_um_05_deactivate_user`**:
    - **Mục tiêu**: Kiểm tra chức năng vô hiệu hóa (deactivate).
    - **Phân tích**: Gửi request đến `delete_users` view. Xác nhận `is_active` chuyển từ `True` sang `False`.
- **`test_ut_um_07_delete_user_actually_deactivates`**:
    - **Mục tiêu**: Xác nhận hành vi thực tế của chức năng "Xóa".
    - **Phân tích**: Hệ thống hiện tại thực hiện "Soft Delete" (chỉ vô hiệu hóa) chứ không xóa bản ghi khỏi DB. Hàm test xác nhận bản ghi vẫn tồn tại nhưng `is_active=False`.

### 3. Nhóm Cập Nhật & Vai Trò (Update & Roles)
- **`test_ut_um_06_reactivate_user`**:
    - **Mục tiêu**: Kiểm tra khả năng kích hoạt lại tài khoản.
    - **Phân tích**: Cập nhật user đang bị vô hiệu hóa với `is_active=True` thông qua `edit_user` view.
- **`test_ut_um_08_assign_role_update_profile`**:
    - **Mục tiêu**: Kiểm tra thay đổi vai trò qua Group.
    - **Phân tích**: Thay đổi nhóm quyền của user từ Student sang Teacher và xác nhận trường `role` trên model User được cập nhật tương ứng.
- **`test_ut_um_13_update_user_role_prefix`**:
    - **Mục tiêu**: Kiểm tra xem `user_code` có đổi prefix khi đổi role không.
    - **Phân tích**: Xác nhận rằng hiện tại `user_code` chỉ sinh ra 1 lần lúc tạo, không đổi lại khi cập nhật role (Behavioral documentation).

### 4. Nhóm Kiểm Tra Dữ Liệu (Validation)
- **`test_ut_um_09_invalid_national_id`**: Kiểm tra độ dài CCCD (phải đủ 12 số).
- **`test_ut_um_10_duplicate_national_id`**: Kiểm tra tính duy nhất của CCCD.
- **`test_ut_um_11_password_mismatch`**: Kiểm tra tính khớp nhau giữa mật khẩu và xác nhận mật khẩu.

### 5. Nhóm Bảo Mật (Security)
- **`test_ut_um_14_unauthorized_access`**: 
    - **Mục tiêu**: Đảm bảo người dùng thường không thể truy cập trang quản lý.
    - **Phân tích**: Logout admin, login user thường và truy cập URL quản lý. Xác nhận nhận mã lỗi 403 Forbidden.

---

### Initial Instruction / Prompt
The tests were developed based on the following directive:
"Read requirements in @test/testUnit.csv, create unit tests, and add more tests in the CSV to cover all cases."

### Key Findings
- **Phone Uniqueness**: Currently, the system accepts duplicate phone numbers (Logged in CSV as a known bug).
- **Deactivation vs Deletion**: The "Delete" functionality in the management view currently performs a soft-delete (deactivation) by setting `is_active=False`.
- **National ID Validation**: Correctly validates for 12 digits and uniqueness.
- **Role-based Validation**: Phone numbers are required for Teacher/Admin roles but optional for Student roles.
