# Test Automation Notes

## Scope
Tai lieu nay tong hop quy trinh viet va chay test cho 4 phan:
- 1.2 ClassCreateView (UT_CL_01..UT_CL_06)
- 1.3 ClassSession.save (UT_CS_01..UT_CS_07)
- 1.4 EnrollStudentView.post (UT_ENR_01..UT_ENR_06)
- 1.5 Class Status State Transition (UT_ST_01..UT_ST_12)

## Cong cu da dung
- Python virtual environment: .venv
- Pytest + pytest-django + pytest-cov
- Django test client (fixture auth_client)
- PowerShell terminal de chay lenh

## Lenh chay test tung file
Chay trong thu muc `Doantotnghiep`.

### 1.2 ClassCreateView
```powershell
& ".\.venv\Scripts\python.exe" -m pytest apps/classes/tests/test_classcreateview_unit.py -v --tb=short
```

### 1.3 ClassSession.save
```powershell
& ".\.venv\Scripts\python.exe" -m pytest apps/classes/tests/test_classsession_unit.py -v --tb=short
```

### 1.4 EnrollStudentView.post
```powershell
& ".\.venv\Scripts\python.exe" -m pytest apps/classes/tests/test_enrollstudentview_unit.py -v --tb=short
```

### 1.5 Class Status State Transition
```powershell
& ".\.venv\Scripts\python.exe" -m pytest apps/classes/tests/test_classstatetransition_unit.py -v --tb=short
```

## Lenh collect de kiem tra 4 file
```powershell
& ".\.venv\Scripts\python.exe" -m pytest apps/classes/tests/test_classcreateview_unit.py apps/classes/tests/test_classsession_unit.py apps/classes/tests/test_enrollstudentview_unit.py apps/classes/tests/test_classstatetransition_unit.py --collect-only -q
```

## Convention dat ten test
- UT_CL_xx: ClassCreateView
- UT_CS_xx: ClassSession save/model behavior
- UT_ENR_xx: Enrollment create flow
- UT_ST_xx: Class status transition matrix

## File map hien tai
- apps/classes/tests/test_classcreateview_unit.py
- apps/classes/tests/test_classsession_unit.py
- apps/classes/tests/test_enrollstudentview_unit.py
- apps/classes/tests/test_classstatetransition_unit.py
- apps/classes/tests/conftest.py
- pytest.ini
- steam_center/settings_test.py

## Ghi chu ket qua quan trong
- Bo test hien tai la bo defect-detection: van co case fail de chi ra gap nghiep vu.
- Nhom fail chinh:
	- Invalid state transitions van dang duoc cho phep.
	- Enrollment cho class CANCELLED/COMPLETED van dang redirect thanh cong.
	- Session date validation (before start/after end) chua raise ValidationError.

## 1.6 Code Coverage Report
### Lenh da chay
```powershell
& ".\.venv\Scripts\python.exe" -m pytest apps/classes/tests/test_classcreateview_unit.py apps/classes/tests/test_classsession_unit.py apps/classes/tests/test_enrollstudentview_unit.py apps/classes/tests/test_classstatetransition_unit.py --cov=apps.classes.tests.test_classcreateview_unit --cov=apps.classes.tests.test_classsession_unit --cov=apps.classes.tests.test_enrollstudentview_unit --cov=apps.classes.tests.test_classstatetransition_unit --cov-report=term-missing --tb=short
```

### Ket qua coverage
- apps/classes/tests/test_classcreateview_unit.py: 100%
- apps/classes/tests/test_classsession_unit.py: 100%
- apps/classes/tests/test_enrollstudentview_unit.py: 100%
- apps/classes/tests/test_classstatetransition_unit.py: 100%
- TOTAL: 100% (365/365)

### Ket qua test trong lan do coverage gan nhat
- 34 passed
- 13 failed
- 4 warnings
