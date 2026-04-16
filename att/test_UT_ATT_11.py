
# Test case: UT_ATT_11
# Mục đích: Kiểm tra giáo viên cập nhật điểm đánh giá vượt quá max (score = 11).
# Logic: Gửi score = 11, kiểm tra không lưu assessment.
# Kết quả mong muốn: API trả về 400, không lưu assessment.
from django.test import TestCase, Client

class TestUT_ATT_11(TestCase):
    def test_UT_ATT_11(self):
        from apps.assessments.models import Assessment
        from apps.class_sessions.models import ClassSession
        from apps.accounts.models import User
        from apps.classes.models import Class
        from apps.curriculum.models import Subject
        from apps.centers.models import Center, Room
        from django.contrib.auth.models import Permission
        client = Client()
        subject = Subject.objects.create(name='Math')
        center = Center.objects.create(name='Main Center')
        room = Room.objects.create(center=center, name='Room 1')
        klass = Class.objects.create(code='C011', name='Test Class 11', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=11)
        teacher = User.objects.create_user(username='teacher11', password='pass', role='Teacher')
        perm = Permission.objects.get(codename='change_assessment')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student11', password='pass', role='Student')
        client.force_login(teacher)
        url = f'/assessments/update/{session.id}/{student.id}/'
        data = {'score': 11}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 400)
        ass = Assessment.objects.filter(session=session, student=student).first()
        self.assertIsNone(ass)
