from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from events.models import Category, Event
from users.models import StudentVerification


User = get_user_model()


class AdminDashboardStatsTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='password123',
        )
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='password123',
        )
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='password123',
        )
        self.category = Category.objects.create(name='Conference')
        self.confirmed_event = Event.objects.create(
            title='Confirmed Event',
            description='Desc',
            date=timezone.now() + timedelta(days=5),
            location='Hall A',
            category=self.category,
            price=Decimal('50.00'),
            capacity=100,
            organizer=self.organizer,
            is_approved=True,
        )
        self.pending_event = Event.objects.create(
            title='Pending Event',
            description='Desc',
            date=timezone.now() + timedelta(days=6),
            location='Hall B',
            category=self.category,
            price=Decimal('30.00'),
            capacity=80,
            organizer=self.organizer,
            is_approved=False,
        )
        Booking.objects.create(
            user=self.user,
            event=self.confirmed_event,
            status=Booking.STATUS_CONFIRMED,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('50.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('50.00'),
            confirmed_at=timezone.now(),
        )
        Booking.objects.create(
            user=self.user,
            event=self.pending_event,
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('30.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('30.00'),
        )
        StudentVerification.objects.create(
            user=self.organizer,
            student_email='organizer@college.edu',
            student_id='STU-ADMIN-01',
            institution_name='Campus College',
            status=StudentVerification.STATUS_PENDING,
        )

    def test_admin_dashboard_stats_exposes_booking_status_counts(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('admin_stats'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_users'], 3)
        self.assertEqual(response.data['total_events'], 2)
        self.assertEqual(response.data['total_bookings'], 2)
        self.assertEqual(response.data['confirmed_bookings'], 1)
        self.assertEqual(response.data['pending_bookings'], 1)
        self.assertEqual(Decimal(str(response.data['total_revenue'])), Decimal('50'))
        self.assertEqual(len(response.data['latest_bookings']), 2)
        self.assertEqual(len(response.data['pending_events']), 1)
        self.assertEqual(response.data['pending_student_verification_count'], 1)

    def test_dashboard_stats_is_admin_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('admin_stats'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
