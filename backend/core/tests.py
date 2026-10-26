from django.test import TestCase
from rest_framework.test import APIClient

from .models import User, Club, Venue, EventRequest, Notification


class EventflowTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.faculty = User.objects.create_user(
            username='faculty1',
            password='pass123',
            email='faculty@example.com',
            role='FACULTY_ADVISOR',
            department='CSE',
        )
        self.hod = User.objects.create_user(
            username='hod1',
            password='pass123',
            email='hod@example.com',
            role='HOD',
            department='CSE',
        )
        self.student = User.objects.create_user(
            username='student1',
            password='pass123',
            email='student@example.com',
            role='STUDENT',
            department='CSE',
        )
        self.other_student = User.objects.create_user(
            username='student2',
            password='pass123',
            email='student2@example.com',
            role='STUDENT',
            department='CSE',
        )

        self.club = Club.objects.create(
            name='Tech Club',
            faculty_advisor=self.faculty,
            hod=self.hod,
            department='CSE',
        )

        self.venue = Venue.objects.create(
            name='Main Hall',
            capacity=100,
            created_by=self.faculty,
            is_active=True,
        )

    def _login(self, username, password):
        response = self.client.post(
            '/api/auth/login/',
            {'username': username, 'password': password},
        )
        self.assertEqual(response.status_code, 200, response.data)

        token = response.data['access']
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

    def _create_event(
        self,
        date='2026-08-14',
        start='14:00',
        end='18:00',
    ):
        return self.client.post('/api/events/', {
            'club': self.club.id,
            'event_name': 'Test Event',
            'venue': self.venue.id,
            'event_date': date,
            'start_time': start,
            'end_time': end,
        })
    def _approve_event_fully(self, event_id):
        self._login('faculty1', 'pass123')
        faculty_response = self.client.post(
            f'/api/events/{event_id}/approve/'
        )
        self.assertEqual(
            faculty_response.status_code, 200, faculty_response.data
        )
        self.assertEqual(
            faculty_response.data['status'], 'PENDING_HOD'
        )

        self._login('hod1', 'pass123')
        hod_response = self.client.post(
            f'/api/events/{event_id}/approve/'
        )
        self.assertEqual(
            hod_response.status_code, 200, hod_response.data
        )
        self.assertEqual(hod_response.data['status'], 'APPROVED')

        return hod_response

    def _create_notification(self, user, event, message):
        return Notification.objects.create(
            user=user,
            event_request=event,
            message=message,
            sent_status='SENT',
        )

    def _create_notification_event(self):
        return EventRequest.objects.create(
            club=self.club,
            requested_by=self.student,
            event_name='Notification Test Event',
            venue=self.venue,
            event_date='2026-08-14',
            start_time='14:00',
            end_time='18:00',
            status='PENDING_FACULTY',
            current_approver=self.faculty,
        )
    # Conflict detection

    def test_non_overlapping_requests_both_succeed(self):
        self._login('student1', 'pass123')
        r1 = self._create_event(start='09:00', end='11:00')
        r2 = self._create_event(start='12:00', end='14:00')

        self.assertEqual(r1.status_code, 201, r1.data)
        self.assertEqual(r2.status_code, 201, r2.data)

    def test_overlapping_request_is_rejected(self):
        self._login('student1', 'pass123')
        r1 = self._create_event(start='14:00', end='18:00')
        r2 = self._create_event(start='15:00', end='17:00')

        self.assertEqual(r1.status_code, 201, r1.data)
        self.assertEqual(r2.status_code, 400, r2.data)

    def test_end_time_before_start_time_is_rejected(self):
        self._login('student1', 'pass123')
        response = self._create_event(start='18:00', end='14:00')

        self.assertEqual(response.status_code, 400, response.data)

    def test_inactive_venue_request_is_rejected(self):
        self.venue.is_active = False
        self.venue.save(update_fields=['is_active'])

        self._login('student1', 'pass123')
        response = self._create_event()

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn('venue', response.data)
    # State machine: valid transitions

    def test_full_approval_chain_reaches_approved(self):
        self._login('student1', 'pass123')
        create_response = self._create_event()

        self.assertEqual(
            create_response.status_code, 201, create_response.data
        )
        event = create_response.data
        self.assertEqual(event['status'], 'PENDING_FACULTY')

        final_response = self._approve_event_fully(event['id'])
        self.assertEqual(final_response.data['status'], 'APPROVED')

    def test_reject_at_faculty_stage_requires_comment(self):
        self._login('student1', 'pass123')
        create_response = self._create_event()
        self.assertEqual(create_response.status_code, 201)

        event_id = create_response.data['id']
        self._login('faculty1', 'pass123')

        r1 = self.client.post(
            f'/api/events/{event_id}/reject/', {}
        )
        self.assertEqual(r1.status_code, 400, r1.data)

        r2 = self.client.post(
            f'/api/events/{event_id}/reject/',
            {'comment': 'Not suitable.'},
        )
        self.assertEqual(r2.status_code, 200, r2.data)
        self.assertEqual(r2.data['status'], 'REJECTED')

    # State machine: invalid transitions blocked

    def test_hod_cannot_approve_before_faculty(self):
        self._login('student1', 'pass123')
        create_response = self._create_event()
        self.assertEqual(create_response.status_code, 201)

        event_id = create_response.data['id']
        self._login('hod1', 'pass123')

        response = self.client.post(
            f'/api/events/{event_id}/approve/'
        )
        self.assertEqual(response.status_code, 403, response.data)

    def test_cannot_act_on_already_approved_request(self):
        self._login('student1', 'pass123')
        create_response = self._create_event()
        self.assertEqual(create_response.status_code, 201)

        event_id = create_response.data['id']
        self._approve_event_fully(event_id)

        self._login('hod1', 'pass123')
        response = self.client.post(
            f'/api/events/{event_id}/approve/'
        )
        self.assertEqual(response.status_code, 400, response.data)

    def test_wrong_faculty_advisor_cannot_approve_another_clubs_request(self):
        User.objects.create_user(
            username='faculty2',
            password='pass123',
            role='FACULTY_ADVISOR',
            department='CSE',
        )

        self._login('student1', 'pass123')
        create_response = self._create_event()
        self.assertEqual(create_response.status_code, 201)

        event_id = create_response.data['id']
        self._login('faculty2', 'pass123')

        response = self.client.post(
            f'/api/events/{event_id}/approve/'
        )
        self.assertEqual(response.status_code, 403, response.data)

        # Cancellation

    def test_student_can_cancel_own_pending_request(self):
        self._login('student1', 'pass123')
        create_response = self._create_event()
        self.assertEqual(create_response.status_code, 201)

        event_id = create_response.data['id']
        response = self.client.post(
            f'/api/events/{event_id}/cancel/'
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['status'], 'CANCELLED')

    def test_cannot_cancel_already_approved_request(self):
        self._login('student1', 'pass123')
        create_response = self._create_event()
        self.assertEqual(create_response.status_code, 201)

        event_id = create_response.data['id']
        self._approve_event_fully(event_id)

        self._login('student1', 'pass123')
        response = self.client.post(
            f'/api/events/{event_id}/cancel/'
        )
        self.assertEqual(response.status_code, 400, response.data)

        # In-app notifications: listing and authentication

    def test_notifications_require_authentication(self):
        response = self.client.get('/api/notifications/')

        self.assertEqual(response.status_code, 401, response.data)

    def test_user_only_sees_their_own_notifications(self):
        event = self._create_notification_event()

        self._create_notification(
            self.student,
            event,
            'Your event request was received.',
        )
        self._create_notification(
            self.other_student,
            event,
            'This notification belongs to another student.',
        )

        self._login('student1', 'pass123')
        response = self.client.get('/api/notifications/')

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]['message'],
            'Your event request was received.',
        )

    def test_notification_response_contains_expected_fields(self):
        event = self._create_notification_event()

        self._create_notification(
            self.student,
            event,
            'Your event request was received.',
        )

        self._login('student1', 'pass123')
        response = self.client.get('/api/notifications/')

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)

        notification = response.data[0]
        self.assertEqual(
            notification['event_name'],
            'Notification Test Event',
        )
        self.assertEqual(
            notification['message'],
            'Your event request was received.',
        )
        self.assertEqual(notification['sent_status'], 'SENT')
        self.assertFalse(notification['is_read'])
        self.assertIn('sent_at', notification)
    # Mark one notification as read

    def test_user_can_mark_own_notification_as_read(self):
        event = self._create_notification_event()
        notification = self._create_notification(
            self.student,
            event,
            'Please review your event request.',
        )

        self._login('student1', 'pass123')
        response = self.client.post(
            f'/api/notifications/{notification.id}/read/'
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['is_read'])

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_user_cannot_mark_another_users_notification_as_read(self):
        event = self._create_notification_event()
        notification = self._create_notification(
            self.other_student,
            event,
            'This notification belongs to another student.',
        )

        self._login('student1', 'pass123')
        response = self.client.post(
            f'/api/notifications/{notification.id}/read/'
        )

        self.assertEqual(response.status_code, 404, response.data)

        notification.refresh_from_db()
        self.assertFalse(notification.is_read)

    # Mark all notifications as read

    def test_mark_all_read_updates_only_current_users_notifications(self):
        event = self._create_notification_event()

        own_unread = self._create_notification(
            self.student,
            event,
            'First unread notification.',
        )
        own_read = self._create_notification(
            self.student,
            event,
            'Already read notification.',
        )
        own_read.is_read = True
        own_read.save(update_fields=['is_read'])

        other_unread = self._create_notification(
            self.other_student,
            event,
            'Another user unread notification.',
        )

        self._login('student1', 'pass123')
        response = self.client.post(
            '/api/notifications/read-all/'
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['updated_count'], 1)

        own_unread.refresh_from_db()
        own_read.refresh_from_db()
        other_unread.refresh_from_db()

        self.assertTrue(own_unread.is_read)
        self.assertTrue(own_read.is_read)
        self.assertFalse(other_unread.is_read)

    # Unread notification count

    def test_unread_count_returns_zero_when_no_notifications(self):
        self._login('student1', 'pass123')

        response = self.client.get('/api/notifications/unread-count/')

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['unread_count'], 0)

    def test_unread_count_counts_only_unread_notifications(self):
        event = self._create_notification_event()

        self._create_notification(
            self.student,
            event,
            'Unread notification.',
        )
        read_notification = self._create_notification(
            self.student,
            event,
            'Read notification.',
        )
        read_notification.is_read = True
        read_notification.save(update_fields=['is_read'])

        self._login('student1', 'pass123')
        response = self.client.get('/api/notifications/unread-count/')

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['unread_count'], 1)

    def test_unread_count_requires_authentication(self):
        response = self.client.get('/api/notifications/unread-count/')

        self.assertEqual(response.status_code, 401, response.data)