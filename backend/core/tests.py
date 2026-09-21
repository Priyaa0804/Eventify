

# Create your tests here.
from django.test import TestCase
from rest_framework.test import APIClient
from .models import User, Club, Venue, EventRequest


class EventflowTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.faculty = User.objects.create_user(
            username='faculty1', password='pass123',
            role='FACULTY_ADVISOR', department='CSE'
        )
        self.hod = User.objects.create_user(
            username='hod1', password='pass123',
            role='HOD', department='CSE'
        )
        self.student = User.objects.create_user(
            username='student1', password='pass123',
            role='STUDENT', department='CSE'
        )
        self.club = Club.objects.create(
            name='Tech Club', faculty_advisor=self.faculty, department='CSE'
        )
        self.venue = Venue.objects.create(
            name='Main Hall', capacity=100, created_by=self.faculty
        )

    def _login(self, username, password):
        response = self.client.post('/api/auth/login/', {
            'username': username, 'password': password
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def _create_event(self, date='2026-08-14', start='14:00', end='18:00'):
        return self.client.post('/api/events/', {
            'club': self.club.id, 'event_name': 'Test Event',
            'venue': self.venue.id, 'event_date': date,
            'start_time': start, 'end_time': end,
        })

    # --- Conflict detection ---

    def test_non_overlapping_requests_both_succeed(self):
        self._login('student1', 'pass123')
        r1 = self._create_event(start='09:00', end='11:00')
        r2 = self._create_event(start='12:00', end='14:00')
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)

    def test_overlapping_request_is_rejected(self):
        self._login('student1', 'pass123')
        r1 = self._create_event(start='14:00', end='18:00')
        r2 = self._create_event(start='15:00', end='17:00')
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 400)

    def test_end_time_before_start_time_is_rejected(self):
        self._login('student1', 'pass123')
        response = self._create_event(start='18:00', end='14:00')
        self.assertEqual(response.status_code, 400)

    # --- State machine: valid transitions ---

    def test_full_approval_chain_reaches_approved(self):
        self._login('student1', 'pass123')
        event = self._create_event().data
        self.assertEqual(event['status'], 'PENDING_FACULTY')

        self._login('faculty1', 'pass123')
        r1 = self.client.post(f"/api/events/{event['id']}/approve/")
        self.assertEqual(r1.data['status'], 'PENDING_HOD')

        self._login('hod1', 'pass123')
        r2 = self.client.post(f"/api/events/{event['id']}/approve/")
        self.assertEqual(r2.data['status'], 'APPROVED')

    def test_reject_at_faculty_stage_requires_comment(self):
        self._login('student1', 'pass123')
        event = self._create_event().data

        self._login('faculty1', 'pass123')
        r1 = self.client.post(f"/api/events/{event['id']}/reject/", {})
        self.assertEqual(r1.status_code, 400)

        r2 = self.client.post(f"/api/events/{event['id']}/reject/", {'comment': 'Not suitable.'})
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data['status'], 'REJECTED')

    # --- State machine: invalid transitions blocked ---

    def test_hod_cannot_approve_before_faculty(self):
        self._login('student1', 'pass123')
        event = self._create_event().data

        self._login('hod1', 'pass123')
        response = self.client.post(f"/api/events/{event['id']}/approve/")
        self.assertEqual(response.status_code, 403)

    def test_cannot_act_on_already_approved_request(self):
        self._login('student1', 'pass123')
        event = self._create_event().data

        self._login('faculty1', 'pass123')
        self.client.post(f"/api/events/{event['id']}/approve/")
        self._login('hod1', 'pass123')
        self.client.post(f"/api/events/{event['id']}/approve/")

        response = self.client.post(f"/api/events/{event['id']}/approve/")
        self.assertEqual(response.status_code, 400)

    def test_wrong_faculty_advisor_cannot_approve_another_clubs_request(self):
        other_faculty = User.objects.create_user(
            username='faculty2', password='pass123',
            role='FACULTY_ADVISOR', department='CSE'
        )
        self._login('student1', 'pass123')
        event = self._create_event().data

        self._login('faculty2', 'pass123')
        response = self.client.post(f"/api/events/{event['id']}/approve/")
        self.assertEqual(response.status_code, 403)

    # --- Cancel ---

    def test_student_can_cancel_own_pending_request(self):
        self._login('student1', 'pass123')
        event = self._create_event().data
        response = self.client.post(f"/api/events/{event['id']}/cancel/")
        self.assertEqual(response.data['status'], 'CANCELLED')

    def test_cannot_cancel_already_approved_request(self):
        self._login('student1', 'pass123')
        event = self._create_event().data
        self._login('faculty1', 'pass123')
        self.client.post(f"/api/events/{event['id']}/approve/")
        self._login('hod1', 'pass123')
        self.client.post(f"/api/events/{event['id']}/approve/")

        self._login('student1', 'pass123')
        response = self.client.post(f"/api/events/{event['id']}/cancel/")
        self.assertEqual(response.status_code, 400)