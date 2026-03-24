from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from events.models import Category, Event


User = get_user_model()


class EventAPITests(APITestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='password123',
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='other',
            password='password123',
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='password123',
        )
        self.category = Category.objects.create(name='Conference')

    def test_event_creation_rejects_invalid_values(self):
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(
            reverse('event-list'),
            {
                'title': '   ',
                'description': 'Test event',
                'date': (timezone.now() - timedelta(days=1)).isoformat(),
                'location': '   ',
                'category': str(self.category.id),
                'price': '-1.00',
                'capacity': 0,
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
        self.assertIn('date', response.data)
        self.assertIn('location', response.data)
        self.assertIn('price', response.data)
        self.assertIn('capacity', response.data)

    def test_event_creation_starts_as_pending_even_if_payload_requests_approval(self):
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(
            reverse('event-list'),
            {
                'title': 'Fresh Event',
                'description': 'Needs review',
                'date': (timezone.now() + timedelta(days=5)).isoformat(),
                'location': 'Conference Hall',
                'category': str(self.category.id),
                'price': '10.00',
                'capacity': 50,
                'is_approved': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_approved'])

    def test_public_event_list_only_includes_approved_events(self):
        approved_event = Event.objects.create(
            title='Approved Event',
            description='Visible to everyone',
            date=timezone.now() + timedelta(days=2),
            location='Hall A',
            category=self.category,
            price=Decimal('20.00'),
            capacity=10,
            organizer=self.organizer,
            is_approved=True,
        )
        Event.objects.create(
            title='Pending Event',
            description='Hidden from guests',
            date=timezone.now() + timedelta(days=3),
            location='Hall B',
            category=self.category,
            price=Decimal('25.00'),
            capacity=20,
            organizer=self.organizer,
            is_approved=False,
        )

        response = self.client.get(reverse('event-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item['id'] for item in response.data}
        self.assertIn(str(approved_event.id), returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_organizer_can_view_unapproved_own_event(self):
        event = Event.objects.create(
            title='Private Draft',
            description='Draft',
            date=timezone.now() + timedelta(days=2),
            location='Hall A',
            category=self.category,
            price=Decimal('20.00'),
            capacity=10,
            organizer=self.organizer,
            is_approved=False,
        )

        self.client.force_authenticate(user=self.organizer)
        response = self.client.get(reverse('event-detail', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(event.id))

    def test_only_organizer_or_admin_can_update_event(self):
        event = Event.objects.create(
            title='Team Event',
            description='Desc',
            date=timezone.now() + timedelta(days=3),
            location='Hall B',
            category=self.category,
            price=Decimal('10.00'),
            capacity=25,
            organizer=self.organizer,
            is_approved=True,
        )

        self.client.force_authenticate(user=self.other_user)
        forbidden_response = self.client.patch(
            reverse('event-detail', args=[event.id]),
            {'title': 'Updated by stranger'},
            format='json',
        )
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        admin_response = self.client.patch(
            reverse('event-detail', args=[event.id]),
            {'title': 'Updated by admin'},
            format='json',
        )
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)

    def test_organizer_can_delete_own_event(self):
        event = Event.objects.create(
            title='Delete Me',
            description='Desc',
            date=timezone.now() + timedelta(days=3),
            location='Hall D',
            category=self.category,
            price=Decimal('10.00'),
            capacity=25,
            organizer=self.organizer,
            is_approved=False,
        )

        self.client.force_authenticate(user=self.organizer)
        response = self.client.delete(reverse('event-detail', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_admin_can_approve_pending_event(self):
        event = Event.objects.create(
            title='Approve Me',
            description='Desc',
            date=timezone.now() + timedelta(days=5),
            location='Main Hall',
            category=self.category,
            price=Decimal('30.00'),
            capacity=100,
            organizer=self.organizer,
            is_approved=False,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse('event-approve', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertTrue(event.is_approved)
        self.assertTrue(response.data['is_approved'])

    def test_non_admin_cannot_approve_event(self):
        event = Event.objects.create(
            title='Approval Lock',
            description='Desc',
            date=timezone.now() + timedelta(days=5),
            location='Main Hall',
            category=self.category,
            price=Decimal('30.00'),
            capacity=100,
            organizer=self.organizer,
            is_approved=False,
        )

        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(reverse('event-approve', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        event.refresh_from_db()
        self.assertFalse(event.is_approved)

    def test_only_admin_can_create_categories(self):
        self.client.force_authenticate(user=self.organizer)
        forbidden_response = self.client.post(
            reverse('category-list'),
            {'name': 'Workshop', 'description': 'Hands-on sessions'},
            format='json',
        )
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        allowed_response = self.client.post(
            reverse('category-list'),
            {'name': 'Workshop', 'description': 'Hands-on sessions'},
            format='json',
        )
        self.assertEqual(allowed_response.status_code, status.HTTP_201_CREATED)

    def test_event_serializer_includes_live_booking_status(self):
        event = Event.objects.create(
            title='Capacity Test',
            description='Desc',
            date=timezone.now() + timedelta(days=4),
            location='Hall C',
            category=self.category,
            price=Decimal('15.00'),
            capacity=2,
            organizer=self.organizer,
            is_approved=True,
        )
        Booking.objects.create(
            user=self.other_user,
            event=event,
            status='CONFIRMED',
            is_student=False,
            total_price=Decimal('15.00'),
        )

        self.client.force_authenticate(user=self.organizer)
        response = self.client.get(reverse('event-detail', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['confirmed_booking_count'], 1)
        self.assertEqual(response.data['remaining_capacity'], 1)
        self.assertFalse(response.data['is_sold_out'])
