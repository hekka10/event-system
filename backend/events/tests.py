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
