import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from apps.curriculum.models import Subject, Module, Lesson, Lecture, Exercise
from apps.curriculum.forms import SubjectForm, ModuleForm, LessonForm, ExerciseForm
from apps.curriculum.filters import SubjectFilter, ModuleFilter, LessonFilter
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestCurriculumModels:
    """TC_CU_01 - TC_CU_08: Kiểm tra logic của các Model trong Chương trình học"""

    def test_tc_cu_01_subject_str(self):
        """TC_CU_01: Kiểm tra hiển thị Môn học"""
        subject = Subject.objects.create(name="Toán học", code="MATH01")
        assert str(subject) == "Toán học"

    def test_tc_cu_02_subject_code_uniqueness(self):
        """TC_CU_02: Ràng buộc duy nhất của Mã môn"""
        Subject.objects.create(name="Toán 1", code="MATH01")
        with pytest.raises(IntegrityError):
            Subject.objects.create(name="Toán 2", code="MATH01")

    def test_tc_cu_03_module_str(self):
        """TC_CU_03: Kiểm tra hiển thị Học phần"""
        subject = Subject.objects.create(name="Toán học", code="MATH01")
        module = Module.objects.create(subject=subject, order=1, title="Đại số")
        assert str(module) == "Toán học - Học phần 1: Đại số"

    def test_tc_cu_04_module_unique_order(self):
        """TC_CU_04: Ràng buộc thứ tự (order) duy nhất trong cùng 1 Môn học"""
        subject = Subject.objects.create(name="Toán học", code="MATH01")
        Module.objects.create(subject=subject, order=1, title="Mô đun 1")
        with pytest.raises(IntegrityError):
            # Cùng subject, cùng order -> Phải lỗi
            Module.objects.create(subject=subject, order=1, title="Mô đun trùng")

    def test_tc_cu_05_lesson_str(self):
        """TC_CU_05: Kiểm tra hiển thị Bài học"""
        subject = Subject.objects.create(name="Toán học", code="MATH01")
        module = Module.objects.create(subject=subject, order=1, title="Đại số")
        lesson = Lesson.objects.create(module=module, order=1, title="Số hữu tỉ")
        assert str(lesson) == "Đại số - Bài 1: Số hữu tỉ"

    def test_tc_cu_06_lesson_unique_order(self):
        """TC_CU_06: Ràng buộc thứ tự (order) duy nhất trong cùng 1 Học phần"""
        subject = Subject.objects.create(name="Toán", code="T1")
        module = Module.objects.create(subject=subject, order=1, title="M1")
        Lesson.objects.create(module=module, order=1, title="Lesson 1")
        with pytest.raises(IntegrityError):
            Lesson.objects.create(module=module, order=1, title="Lesson 1 duplicate")

    def test_tc_cu_07_lesson_onetoone_constraints(self):
        """TC_CU_07: Quan hệ 1-1 giữa Lesson và Lecture/Exercise"""
        subject = Subject.objects.create(name="Toán", code="T1")
        module = Module.objects.create(subject=subject, order=1, title="M1")
        lesson = Lesson.objects.create(module=module, order=1, title="L1")
        
        Lecture.objects.create(lesson=lesson, content="Content 1")
        with pytest.raises(IntegrityError):
            # Thêm bài giảng thứ 2 cho cùng 1 bài học -> Lỗi
            Lecture.objects.create(lesson=lesson, content="Content 2")

    def test_tc_cu_08_cascade_delete(self):
        """TC_CU_08: Kiểm tra xóa dây chuyền (Cascade Delete)"""
        subject = Subject.objects.create(name="Toán", code="T1")
        module = Module.objects.create(subject=subject, order=1, title="M1")
        lesson = Lesson.objects.create(module=module, order=1, title="L1")
        Lecture.objects.create(lesson=lesson, content="Lecture")
        Exercise.objects.create(lesson=lesson, description="Exercise")
        
        subject.delete()
        
        assert Module.objects.count() == 0
        assert Lesson.objects.count() == 0
        assert Lecture.objects.count() == 0
        assert Exercise.objects.count() == 0


@pytest.mark.django_db
class TestCurriculumForms:
    """TC_CU_09 - TC_CU_12: Kiểm tra validation và lưu trữ trong các Form"""

    def test_tc_cu_09_subject_form_valid_save(self):
        """Kiểm tra SubjectForm lưu dữ liệu hợp lệ vào DB"""
        data = {'name': 'Môn học mới', 'code': 'NEW_SUB', 'description': 'Mô tả'}
        form = SubjectForm(data=data)
        assert form.is_valid()
        subject = form.save()
        assert Subject.objects.filter(code='NEW_SUB').exists()
        assert subject.name == 'Môn học mới'

    def test_tc_cu_09_subject_form_duplicate_code(self):
        """TC_CU_09: Kiểm tra tính duy nhất của Mã trong SubjectForm"""
        Subject.objects.create(name="Môn 1", code="EXISTING")
        data = {'name': 'Môn 2', 'code': 'EXISTING', 'description': ''}
        form = SubjectForm(data=data)
        assert not form.is_valid()
        assert 'code' in form.errors

    def test_tc_cu_10_module_form_valid_save(self):
        """Kiểm tra ModuleForm lưu dữ liệu hợp lệ vào DB"""
        subject = Subject.objects.create(name="Toán", code="T1")
        data = {'subject': subject.id, 'order': 1, 'title': 'Học phần 1', 'description': ''}
        form = ModuleForm(data=data)
        assert form.is_valid()
        module = form.save()
        assert Module.objects.filter(subject=subject, order=1).exists()
        assert module.title == 'Học phần 1'

    def test_tc_cu_10_module_form_order_validation(self):
        """TC_CU_10: Kiểm tra giá trị thứ tự (order) âm"""
        subject = Subject.objects.create(name="Toán", code="T1")
        data = {'subject': subject.id, 'order': -1, 'title': 'Học phần 1'}
        form = ModuleForm(data=data)
        assert not form.is_valid()
        assert 'order' in form.errors

    def test_tc_cu_11_lesson_form_valid_save(self):
        """Kiểm tra LessonForm lưu dữ liệu hợp lệ vào DB"""
        subject = Subject.objects.create(name="Toán", code="T1")
        module = Module.objects.create(subject=subject, order=1, title="M1")
        data = {'module': module.id, 'order': 1, 'title': 'Bài 1', 'objectives': ''}
        form = LessonForm(data=data)
        assert form.is_valid()
        lesson = form.save()
        assert Lesson.objects.filter(module=module, order=1).exists()

    def test_tc_cu_11_lesson_form_required_module(self):
        """TC_CU_11: Kiểm tra bắt buộc chọn Học phần trong LessonForm"""
        data = {'module': '', 'order': 1, 'title': 'Bài 1'}
        form = LessonForm(data=data)
        assert not form.is_valid()
        assert 'module' in form.errors

    def test_tc_cu_12_exercise_form_difficulty_choices(self):
        """TC_CU_12: Kiểm tra độ khó (Difficulty) trong ExerciseForm"""
        subject = Subject.objects.create(name="Toán", code="T1")
        module = Module.objects.create(subject=subject, order=1, title="M1")
        lesson = Lesson.objects.create(module=module, order=1, title="L1")
        
        data = {
            'lesson': lesson.id,
            'description': 'Test',
            'difficulty': 'invalid_choice'
        }
        form = ExerciseForm(data=data)
        assert not form.is_valid()
        assert 'difficulty' in form.errors


@pytest.mark.django_db
class TestCurriculumFilters:
    """TC_CU_13 - TC_CU_16: Kiểm tra các bộ lọc (FilterSet)"""

    @pytest.fixture
    def setup_data(self):
        s1 = Subject.objects.create(name="Toán học", code="TOAN", description="Môn toán")
        s2 = Subject.objects.create(name="Vật lý", code="LY", description="Môn lý")
        m1 = Module.objects.create(subject=s1, order=1, title="Đại số")
        m2 = Module.objects.create(subject=s2, order=1, title="Cơ học")
        Lesson.objects.create(module=m1, order=1, title="Số hữu tỉ")
        Lesson.objects.create(module=m2, order=1, title="Chuyển động")

    def test_tc_cu_13_subject_filter_search(self, setup_data):
        """TC_CU_13: Tìm kiếm Môn học theo từ khóa"""
        qs = Subject.objects.all()
        f = SubjectFilter({'query': 'Toán'}, queryset=qs)
        assert f.qs.count() == 1
        assert f.qs[0].code == "TOAN"

    def test_tc_cu_14_module_filter_by_subject(self, setup_data):
        """TC_CU_14: Lọc Học phần theo Môn học"""
        subject_toan = Subject.objects.get(code="TOAN")
        qs = Module.objects.all()
        f = ModuleFilter({'subject': subject_toan.id}, queryset=qs)
        assert f.qs.count() == 1
        assert f.qs[0].title == "Đại số"

    def test_tc_cu_15_lesson_filter_has_lecture(self, setup_data):
        """TC_CU_15: Lọc bài học có bài giảng"""
        lesson = Lesson.objects.get(title="Số hữu tỉ")
        Lecture.objects.create(lesson=lesson, content="Bài giảng số hữu tỉ")
        
        qs = Lesson.objects.all()
        f = LessonFilter({'has_lecture': 'yes'}, queryset=qs)
        assert f.qs.count() == 1
        assert f.qs[0].title == "Số hữu tỉ"

    def test_tc_cu_16_lesson_filter_dynamic_queryset(self, setup_data):
        """TC_CU_16: Kiểm tra lọc động Học phần dựa trên Môn học đã chọn trong Filter Form"""
        subject_toan = Subject.objects.get(code="TOAN")
        # Khởi tạo filter với dữ liệu subject là Toán
        f = LessonFilter(data={'subject': subject_toan.id})
        # Queryset của field 'module' trong form phải chỉ chứa các module của môn Toán
        module_queryset = f.form.fields['module'].queryset
        assert module_queryset.count() == 1
        assert module_queryset[0].title == "Đại số"


@pytest.mark.django_db
class TestCurriculumSignals:
    """TC_CU_17 - TC_CU_18: Kiểm tra Signal xóa file"""

    def test_tc_cu_17_lecture_file_delete_on_delete(self):
        """TC_CU_17: Xóa file bài giảng khi xóa bản ghi Lecture"""
        # Mock storage của field 'file' trong Lecture
        file_field = Lecture._meta.get_field('file')
        original_storage = file_field.storage
        mock_storage = MagicMock()
        mock_storage.save.return_value = "lectures/test.pdf"
        mock_storage.generate_filename = lambda n: n
        file_field.storage = mock_storage
        
        try:
            subject = Subject.objects.create(name="T", code="T")
            module = Module.objects.create(subject=subject, order=1, title="M")
            lesson = Lesson.objects.create(module=module, order=1, title="L")
            
            fake_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
            lecture = Lecture.objects.create(lesson=lesson, file=fake_file)
            
            with patch.object(lecture.file, 'delete') as mock_file_delete:
                lecture.delete()
                mock_file_delete.assert_called_once_with(save=False)
        finally:
            file_field.storage = original_storage

    def test_tc_cu_18_lecture_file_delete_on_change(self):
        """TC_CU_18: Xóa file cũ khi cập nhật file mới trong Lecture"""
        file_field = Lecture._meta.get_field('file')
        original_storage = file_field.storage
        
        # Tạo Mock Storage
        mock_storage = MagicMock()
        # Mock trả về tên file khi save
        mock_storage.save.side_effect = ["lectures/old.pdf", "lectures/new.pdf"]
        mock_storage.generate_filename = lambda n: n
        # Quan trọng: Mock hàm exists để Django không thử kiểm tra file trên cloud
        mock_storage.exists.return_value = False
        
        file_field.storage = mock_storage
        
        try:
            subject = Subject.objects.create(name="T", code="T")
            module = Module.objects.create(subject=subject, order=1, title="M")
            lesson = Lesson.objects.create(module=module, order=1, title="L")
            
            # 1. Tạo bản ghi với file cũ
            old_file = SimpleUploadedFile("old.pdf", b"old content")
            lecture = Lecture.objects.create(lesson=lesson, file=old_file)
            
            # Reset mock để không tính lần gọi lúc khởi tạo (nếu có)
            mock_storage.delete.reset_mock()
            
            # 2. Cập nhật file mới
            new_file = SimpleUploadedFile("new.pdf", b"new content")
            lecture.file = new_file
            lecture.save()
            
            # 3. Kiểm tra xem Signal có gọi storage.delete() để xóa 'lectures/old.pdf' không
            # Lưu ý: Signal gọi file_field.delete(save=False), bên trong đó gọi storage.delete(name)
            mock_storage.delete.assert_called_once_with("lectures/old.pdf")
            
        finally:
            file_field.storage = original_storage
