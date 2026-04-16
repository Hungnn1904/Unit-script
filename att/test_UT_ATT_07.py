
# Test case: UT_ATT_07
# Mục đích: Kiểm tra update hợp lệ lần 1, lần 2 gửi status không hợp lệ.
# Logic: Lần 1 gửi status='P' (hợp lệ), lần 2 gửi status='Sick' (không hợp lệ).
# Kết quả mong muốn: Lần 2 không update, dữ liệu giữ nguyên.
from django.test import TestCase, Client

class TestUT_ATT_07(TestCase):
    def test_UT_ATT_07(self):
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
        klass = Class.objects.create(code='C007', name='Test Class 7', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=7)
        teacher = User.objects.create_user(username='teacher7', password='pass', role='Teacher')
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='change_attendance')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student11', password='pass', role='Student')

        client.force_login(teacher)
        url = f'/attendance/update/{session.id}/{student.id}/'
        data1 = {'status': 'P'}
        response1 = client.post(url, data1)
        self.assertEqual(response1.status_code, 200)
        att1 = Attendance.objects.filter(session=session, student=student).first()
        self.assertIsNotNone(att1)
        self.assertEqual(att1.status, 'P')
        data2 = {'status': 'Sick'}
        response2 = client.post(url, data2)
        self.assertEqual(response2.status_code, 400)
        att2 = Attendance.objects.filter(session=session, student=student).first()
        self.assertIsNotNone(att2)
        self.assertEqual(att2.status, 'P')
