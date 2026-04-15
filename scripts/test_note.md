# Test Automation Notes

## Scope (4 file da sua)
Tai lieu nay tong hop theo 4 file test trong thu muc scripts:
- test_classcreateview_unit.py (UT_CL_01..UT_CL_06 + add_sec1)
- test_classsession_unit.py (UT_CS_01..UT_CS_07 + add_sec2)
- test_enrollstudentview_unit.py (UT_ENR_01..UT_ENR_06 + add_sec3)
- test_classstatetransition_unit.py (UT_ST_01..UT_ST_12 + add_sec4)

## Muc tieu tung nhom test
1. ClassCreateView
- Kiem tra EP/BVA cho create class: bien ngay bat dau-ket thuc, thieu field bat buoc, duplicate code, invalid status.
- Xac nhan status code 204/422 va DB khong tao ban ghi sai.

2. ClassSession.save
- Kiem tra session date hop le, date o bien start/end, duplicate index, class khong co date.
- Co case mong doi ValidationError cho date ngoai khoang lop (de bat gap validation neu chua implement).

3. EnrollStudentView.post
- Decision table theo trang thai lop: PLANNED/ONGOING cho phep, CANCELLED/COMPLETED tu choi.
- Kiem tra duplicate enrollment va invalid student id.

4. State transition class status
- Phu ma tran chuyen trang thai giua PLANNED, ONGOING, COMPLETED, CANCELLED.
- Tach ro case valid va invalid transition qua endpoint class_edit.

## Convention dat ten
- UT_CL_xx: Class create view/form
- UT_CS_xx: Class session model behavior
- UT_ENR_xx: Enrollment create flow
- UT_ST_xx: Class status transition
- test_add_secX_*: case bo sung de tang do phu va phuc vu bao cao

## Lenh chay test (PowerShell)
### Chay tung file
```powershell
.\.venv\Scripts\python.exe -m pytest scripts\test_classcreateview_unit.py -v --tb=short
.\.venv\Scripts\python.exe -m pytest scripts\test_classsession_unit.py -v --tb=short
.\.venv\Scripts\python.exe -m pytest scripts\test_enrollstudentview_unit.py -v --tb=short
.\.venv\Scripts\python.exe -m pytest scripts\test_classstatetransition_unit.py -v --tb=short
```

### Chay ca 4 file
```powershell
.\.venv\Scripts\python.exe -m pytest scripts\test_classcreateview_unit.py scripts\test_classsession_unit.py scripts\test_enrollstudentview_unit.py scripts\test_classstatetransition_unit.py -v --tb=short
```

### Chay theo nhom UT
```powershell
.\.venv\Scripts\python.exe -m pytest scripts\test_classcreateview_unit.py -k "ut_cl" -v --tb=short
.\.venv\Scripts\python.exe -m pytest scripts\test_classsession_unit.py -k "ut_cs" -v --tb=short
.\.venv\Scripts\python.exe -m pytest scripts\test_enrollstudentview_unit.py -k "ut_enr" -v --tb=short
.\.venv\Scripts\python.exe -m pytest scripts\test_classstatetransition_unit.py -k "ut_st" -v --tb=short
```

### Chay 1 test cu the (vi du)
```powershell
.\.venv\Scripts\python.exe -m pytest scripts\test_classstatetransition_unit.py::test_ut_st_01_planned_to_ongoing -v --tb=short
```

### Kiem tra collect
```powershell
.\.venv\Scripts\python.exe -m pytest scripts\test_classcreateview_unit.py scripts\test_classsession_unit.py scripts\test_enrollstudentview_unit.py scripts\test_classstatetransition_unit.py --collect-only -q
```

## Ghi chu ket qua mong doi
- Cac case invalid transition trong nhom UT_ST duoc thiet ke de phat hien lo hong validate state machine.
- Cac case deny enrollment voi class CANCELLED/COMPLETED duoc thiet ke de phat hien sai lech rule nghiep vu neu he thong van tao ghi danh.
- Cac case add_sec1..add_sec4 la bo sung regression/smoke nhe de bao dam endpoint hoat dong on dinh.

## File map hien tai
- scripts/test_classcreateview_unit.py
- scripts/test_classsession_unit.py
- scripts/test_enrollstudentview_unit.py
- scripts/test_classstatetransition_unit.py
- scripts/test_note.md
