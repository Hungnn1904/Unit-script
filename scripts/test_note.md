# Test Automation Notes

## Scope
Tài liệu này tổng hợp quy trình viết và chạy test cho 4 nhóm:
- ClassCreateView (UT_CL_01..UT_CL_06)
- ClassSession.save (UT_CS_01..UT_CS_07)
- EnrollStudentView / Enrollment create (UT_ENR_01..UT_ENR_06)
- State Transition class status (UT_ST_01..UT_ST_12)

## Công cụ đã dùng
- Python virtual environment: .venv
- Pytest + pytest-django
- Django test client (fixture auth_client)
- VS Code + GitHub Copilot chat workflow
- PowerShell terminal để chạy lệnh

## Lệnh đã dùng để chạy test
### Chạy toàn bộ Class tests
```powershell
.\.venv\Scripts\python.exe -m pytest apps/classes/tests/test_classes_unit.py -v --tb=short
```

### Chạy toàn bộ EnrollStudentView tests
```powershell
.\.venv\Scripts\python.exe -m pytest apps/classes/tests/test_enrollstudentview_unit.py -v --tb=short
```

### Chạy theo nhóm (ví dụ State Transition)
```powershell
.\.venv\Scripts\python.exe -m pytest apps/classes/tests/test_classes_unit.py -k "ut_st" -v --tb=short
```

### Chạy test đơn lẻ (ví dụ)
```powershell
.\.venv\Scripts\python.exe -m pytest apps/classes/tests/test_classes_unit.py::test_ut_st_01_planned_to_ongoing -v --tb=short
```

### Kiểm tra collect test
```powershell
.\.venv\Scripts\python.exe -m pytest apps/classes/tests/test_classes_unit.py apps/classes/tests/test_enrollstudentview_unit.py --collect-only -q
```

## Prompt patterns đã sử dụng
Dưới đây là các mẫu prompt đã dùng để tạo và mở rộng test:

1) Prompt tạo test EP/BVA cho create class
- "Thêm vào test_classes_unit.py các case UT_CL_xx cho end_date boundary, required fields, duplicate code..."

2) Prompt tạo test ClassSession.save
- "Viết UT_CS_xx cho valid date, boundary start/end, duplicate index, null date handling..."

3) Prompt tạo test EnrollStudentView theo decision table
- "Viết UT_ENR_xx cho class status Ongoing/Planned/Cancelled/Completed và duplicate enrollment..."

4) Prompt tạo test State Transition full matrix
- "Phủ kín UT_ST_01..UT_ST_12 cho 12 chuyển đổi chéo giữa PLANNED/ONGOING/COMPLETED/CANCELLED..."

5) Prompt vận hành
- "Chạy riêng từng test cho tôi"
- "Chạy lại nhóm ut_st"
- "Tổng hợp lại script test"

## Convention đặt tên test
- UT_CL_xx: Class create form/view
- UT_CS_xx: ClassSession save/model behavior
- UT_ENR_xx: Enrollment create flow
- UT_ST_xx: Class status transition matrix

## File map
- apps/classes/tests/test_classes_unit.py
- apps/classes/tests/test_enrollstudentview_unit.py
- apps/classes/tests/conftest.py
- pytest.ini
- steam_center/settings_test.py

## Ghi chú kết quả quan trọng
- Nhiều case invalid transition (UT_ST) đang fail, chỉ ra gap validation trong luồng class_edit.
- Các case deny enrollment cho class CANCELLED/COMPLETED cũng phát hiện gap nghiệp vụ (hệ thống vẫn redirect thành công).
- Các note/section header đã được thêm vào file test để dễ bảo trì và báo cáo.
