import time
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.centers.models import Center
from apps.curriculum.models import Subject

User = get_user_model()

class ShowcaseTest(TestCase):
    # ANSI Colors for beautiful logs
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

    def log_header(self, title):
        print(f"\n{self.BOLD}{self.BLUE}{'='*60}")
        print(f"SECTION: {title}")
        print(f"{'='*60}{self.ENDC}")

    def log_case(self, tc_id, objective):
        print(f"\n{self.BOLD}▶ [{tc_id}] {objective}{self.ENDC}")

    def log_step(self, msg):
        time.sleep(0.3)
        print(f"   {self.GREEN}Step: {msg}{self.ENDC}")

    def log_info(self, label, value):
        print(f"   {self.YELLOW}Info: {label} -> {value}{self.ENDC}")

    def log_bug(self, msg):
        print(f"   {self.RED}{self.BOLD}[BUG FOUND] ⚠ {msg}{self.ENDC}")

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', password='1')
        self.client.login(username='admin', password='1')
        
        self.center = Center.objects.create(name='EDS-HN')
        self.subject = Subject.objects.create(name='STEAM Robotics', code='SR01')
        self.teacher = User.objects.create(username='teacher1', role='TEACHER', is_active=True)
        self.student = User.objects.create(username='student1', role='STUDENT', is_active=True)
        self.student.set_password('123')
        self.student.save()
        
        self.teacher_group = Group.objects.create(name='Teacher')
        self.student_group = Group.objects.create(name='Student')

    def test_section_create_views(self):
        self.log_header("1.2 USER & CLASS CREATION LOGIC")
        
        self.log_case("UT_UM_01", "Create Teacher with valid data")
        self.log_step("POST /accounts/add/ with Group='Teacher'")
        data = {
            'first_name': 'Nguyen', 'last_name': 'An', 'email': 'an@eds.com',
            'phone': '0912345678', 'password1': '123', 'password2': '123',
            'gender': 'M', 'dob': '1995-01-01', 'national_id': '001200300400',
            'address': 'Hanoi', 'groups': [self.teacher_group.id], 'center': self.center.id
        }
        resp = self.client.post(reverse('accounts:add_user'), data)
        self.assertEqual(resp.status_code, 200)
        
        # In forms.py: slugify("Nguyen An") -> "nguyen-an"
        user = User.objects.get(username='nguyen-an')
        self.log_info("Result", f"HTTP {resp.status_code}")
        self.log_info("Auto-Generated Code", user.user_code)
        self.assertEqual(user.role, 'Teacher')

        self.log_case("UT_UM_02", "Negative Testing: Duplicate Phone Number")
        self.log_step(f"Attempting to register another user with same phone: '0912345678'")
        data['first_name'] = 'Nguyen'
        data['last_name'] = 'Binh'
        data['email'] = 'binh@eds.com'
        data['national_id'] = '001200300401'
        resp = self.client.post(reverse('accounts:add_user'), data)
        count = User.objects.filter(phone='0912345678').count()
        self.log_info("Phone Count in DB", count)
        if count > 1:
            self.log_bug("System failed to block duplicate phone number!")

    def test_section_state_transition(self):
        self.log_header("1.3 USER STATE & SOFT DELETE")
        
        self.log_case("UT_UM_05", "Deactivate User (Active -> Inactive)")
        self.log_step(f"Current Status of {self.teacher.username}: is_active={self.teacher.is_active}")
        self.client.post(reverse('accounts:delete_users'), {'single_user_id': self.teacher.id})
        self.teacher.refresh_from_db()
        self.log_info("New Status", f"is_active={self.teacher.is_active}")
        
        self.log_case("UT_UM_07", "Verify 'Delete' functionality behavior")
        exists = User.objects.filter(id=self.teacher.id).exists()
        self.log_info("Record exists in DB", exists)
        if exists and not self.teacher.is_active:
            self.log_info("Note", "Confirmed: View uses 'Soft Delete' (Deactivation) logic.")

    def test_section_decision_table(self):
        self.log_header("1.4 DECISION TABLE: ROLE VS PHONE VALIDATION")
        
        # Case 1: Teacher + No Phone -> Reject
        self.log_case("UT_UM_03", "Condition: Role=Teacher, Phone=Empty")
        data = {
            'first_name': 'Nguyen', 'last_name': 'Xuan', 'email': 'xuan@eds.com',
            'gender': 'M', 'dob': '1990-01-01', 'national_id': '001200300402',
            'address': 'Hanoi', 'groups': [self.teacher_group.id],
            'phone': '', 'password1': '1', 'password2': '1'
        }
        resp = self.client.post(reverse('accounts:add_user'), data)
        self.log_info("Action", "System Rejected (400 Bad Request)")
        self.assertEqual(resp.status_code, 400)

        # Case 2: Student + No Phone -> Accept
        self.log_case("UT_UM_12", "Condition: Role=Student, Phone=Empty")
        data['groups'] = [self.student_group.id]
        data['national_id'] = '001200300403'
        data['email'] = 'xuan2@eds.com'
        resp = self.client.post(reverse('accounts:add_user'), data)
        self.log_info("Action", f"System Status Code: {resp.status_code}")
        self.assertEqual(resp.status_code, 200)

    def test_section_security(self):
        self.log_header("1.5 SECURITY & ACCESS CONTROL")
        self.log_case("UT_UM_14", "Regular Student access Admin Management")
        self.client.logout()
        success = self.client.login(username='student1', password='123')
        self.log_step(f"Student login success: {success}")
        
        self.log_step("Student attempting to access /accounts/manage/")
        resp = self.client.get(reverse('accounts:manage_accounts'))
        self.log_info("Status Code", resp.status_code)
        if resp.status_code == 403:
            self.log_step("Access Blocked. Security Policy Verified.")
        self.assertEqual(resp.status_code, 403)
