
# Test case: UT_ATT_05
# Mục đích: Kiểm tra cập nhật điểm danh với note (ghi chú) hợp lệ.
# Logic: Tạo dữ liệu, gán quyền, gửi request với status='L' và note.
# Kết quả mong muốn: Attendance lưu đúng status và note.
from django.test import TestCase, Client

class TestUT_ATT_05(TestCase):
    def test_UT_ATT_05(self):
        from apps.attendance.models import Attendance
        from apps.class_sessions.models import ClassSession
        from apps.accounts.models import User
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room

        client = Client()
        subject = Subject.objects.create(name='Math')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C005', name='Test Class 5', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=5)
        teacher = User.objects.create_user(username='teacher5', password='pass', role='Teacher')
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='change_attendance')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student9', password='pass', role='Student')

        client.force_login(teacher)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data = {'status': 'L', 'note': 'Đi muộn do tắc đường'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 200)
        att = Attendance.objects.filter(session=session, student=student).first()
        self.assertIsNotNone(att)
        self.assertEqual(att.status, 'L')
        self.assertEqual(att.note, 'Đi muộn do tắc đường')
