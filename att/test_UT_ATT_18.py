
# Test case: UT_ATT_18
# Mục đích: Kiểm tra giáo viên cập nhật remark mà không có score.
# Logic: Gửi remark, không gửi score, kiểm tra lưu assessment với score=None.
# Kết quả mong muốn: Assessment được tạo, score=None.
from django.test import TestCase, Client

class TestUT_ATT_18(TestCase):
    def test_UT_ATT_18(self):
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
        klass = Class.objects.create(code='C018', name='Test Class 18', center=center, subject=subject, room=room)
        session = ClassSession.objects.create(klass=klass, index=18)
        teacher = User.objects.create_user(username='teacher18', password='pass', role='Teacher')
        perm = Permission.objects.get(codename='change_assessment')
        teacher.user_permissions.add(perm)
        teacher.save()
        student = User.objects.create_user(username='student18', password='pass', role='Student')
        client.force_login(teacher)
        url = f'/assessments/update/{session.id}/{student.id}/'
        data = {'remark': 'No score'}
        response = client.post(url, data)
        self.assertEqual(response.status_code, 200)
        ass = Assessment.objects.filter(session=session, student=student).first()
        self.assertIsNotNone(ass)
        self.assertIsNone(ass.score)
