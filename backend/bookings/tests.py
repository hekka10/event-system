from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from events.models import Category, Event

from .models import Booking, Payment, Ticket


User = get_user_model()


class BookingWorkflowTests(APITestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='password123',
        )
        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            username='attendee',
            password='password123',
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='password123',
        )
        self.category = Category.objects.create(name='Conference')
        self.event = Event.objects.create(
            title='Tech Summit',
            description='Conference',
            date=timezone.now() + timedelta(days=5),
            location='Main Hall',
            category=self.category,
            price=Decimal('50.00'),
            capacity=100,
            organizer=self.organizer,
            is_approved=True,
        )

    def test_unauthenticated_users_cannot_create_or_pay_for_bookings(self):
        create_response = self.client.post(
            reverse('booking-list'),
            {'event': str(self.event.id)},
            format='json',
        )
        initiate_response = self.client.post(
            reverse('payment_initiate'),
            {'event': str(self.event.id)},
            format='json',
        )

        self.assertEqual(create_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(initiate_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_booking_create_starts_pending_and_calculates_price(self):
        self.client.force_authenticate(user=self.attendee)

        response = self.client.post(
            reverse('booking-list'),
            {'event': str(self.event.id)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(pk=response.data['id'])
        self.assertEqual(booking.status, Booking.STATUS_PENDING)
        self.assertEqual(booking.total_price, Decimal('50.00'))
        self.assertEqual(response.data['status'], Booking.STATUS_PENDING)

    def test_booking_create_blocks_duplicate_active_booking(self):
        Booking.objects.create(
            user=self.attendee,
            event=self.event,
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('50.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('50.00'),
        )

        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(
            reverse('booking-list'),
            {'event': str(self.event.id)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already booked this event', str(response.data))

    def test_booking_update_endpoint_is_not_available(self):
        booking = Booking.objects.create(
            user=self.attendee,
            event=self.event,
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('50.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('50.00'),
        )

        self.client.force_authenticate(user=self.attendee)
        response = self.client.patch(
            reverse('booking-detail', args=[booking.id]),
            {'status': Booking.STATUS_CONFIRMED},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_payment_initiation_blocks_full_event(self):
        sold_out_event = Event.objects.create(
            title='Sold Out Session',
            description='Conference',
            date=timezone.now() + timedelta(days=6),
            location='Room 2',
            category=self.category,
            price=Decimal('20.00'),
            capacity=1,
            organizer=self.organizer,
            is_approved=True,
        )
        Booking.objects.create(
            user=self.organizer,
            event=sold_out_event,
            status=Booking.STATUS_CONFIRMED,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('20.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('20.00'),
            confirmed_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(
            reverse('payment_initiate'),
            {'event': str(sold_out_event.id)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('full capacity', str(response.data))

    def test_second_payment_confirmation_is_blocked_when_last_seat_is_taken(self):
        limited_event = Event.objects.create(
            title='Limited Session',
            description='One seat only',
            date=timezone.now() + timedelta(days=7),
            location='VIP Room',
            category=self.category,
            price=Decimal('40.00'),
            capacity=1,
            organizer=self.organizer,
            is_approved=True,
        )
        second_attendee = User.objects.create_user(
            email='attendee2@example.com',
            username='attendee2',
            password='password123',
        )

        first_booking = Booking.objects.create(
            user=self.attendee,
            event=limited_event,
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('40.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('40.00'),
        )
        second_booking = Booking.objects.create(
            user=second_attendee,
            event=limited_event,
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('40.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('40.00'),
        )
        first_payment = Payment.objects.create(
            booking=first_booking,
            user=self.attendee,
            provider=Payment.PROVIDER_MOCK,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('40.00'),
            external_reference='PAY-FIRST-SEAT',
            checkout_url='http://localhost:5173/checkout/first',
        )
        second_payment = Payment.objects.create(
            booking=second_booking,
            user=second_attendee,
            provider=Payment.PROVIDER_MOCK,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('40.00'),
            external_reference='PAY-SECOND-SEAT',
            checkout_url='http://localhost:5173/checkout/second',
        )

        self.client.force_authenticate(user=self.attendee)
        first_response = self.client.post(
            reverse('payment_verify', args=[first_payment.id]),
            {'status': Payment.STATUS_SUCCESS},
            format='json',
        )

        self.client.force_authenticate(user=second_attendee)
        second_response = self.client.post(
            reverse('payment_verify', args=[second_payment.id]),
            {'status': Payment.STATUS_SUCCESS},
            format='json',
        )

        first_booking.refresh_from_db()
        second_booking.refresh_from_db()
        second_payment.refresh_from_db()

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(first_booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(second_booking.status, Booking.STATUS_FAILED)
        self.assertEqual(second_payment.status, Payment.STATUS_FAILED)
        self.assertIn('full capacity', str(second_response.data))

    def test_payment_initiation_creates_pending_booking_and_payment(self):
        self.client.force_authenticate(user=self.attendee)

        response = self.client.post(
            reverse('payment_initiate'),
            {'event': str(self.event.id)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['next_action'], 'COMPLETE_PAYMENT')
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Booking.objects.first().status, Booking.STATUS_PENDING)
        self.assertEqual(Payment.objects.first().status, Payment.STATUS_INITIATED)

    def test_payment_verification_confirms_booking_and_generates_ticket(self):
        booking = Booking.objects.create(
            user=self.attendee,
            event=self.event,
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('50.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('50.00'),
        )
        payment = Payment.objects.create(
            booking=booking,
            user=self.attendee,
            provider=Payment.PROVIDER_MOCK,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('50.00'),
            external_reference='PAY-TEST-VERIFY',
            checkout_url='http://localhost:5173/checkout/test',
        )

        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(
            reverse('payment_verify', args=[payment.id]),
            {
                'status': Payment.STATUS_SUCCESS,
                'provider_reference': 'SANDBOX-123',
                'provider_response': {'gateway': 'sandbox'},
            },
            format='json',
        )

        booking.refresh_from_db()
        payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(payment.status, Payment.STATUS_SUCCESS)
        ticket = Ticket.objects.get(booking=booking)
        self.assertTrue(ticket.ticket_code.startswith('TICKET-'))
        self.assertTrue(bool(ticket.qr_code))
        self.assertIn('qr_code_url', response.data['booking']['ticket'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].attachments)

    def test_confirmed_bookings_receive_unique_ticket_codes(self):
        first_booking = Booking.objects.create(
            user=self.attendee,
            event=self.event,
            status=Booking.STATUS_CONFIRMED,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('50.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('50.00'),
            confirmed_at=timezone.now(),
        )
        second_user = User.objects.create_user(
            email='another@example.com',
            username='another',
            password='password123',
        )
        second_event = Event.objects.create(
            title='Backend Expo',
            description='Conference',
            date=timezone.now() + timedelta(days=10),
            location='Expo Hall',
            category=self.category,
            price=Decimal('30.00'),
            capacity=100,
            organizer=self.organizer,
            is_approved=True,
        )
        second_booking = Booking.objects.create(
            user=second_user,
            event=second_event,
            status=Booking.STATUS_CONFIRMED,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('30.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('30.00'),
            confirmed_at=timezone.now(),
        )

        first_ticket = Ticket.objects.create(booking=first_booking)
        second_ticket = Ticket.objects.create(booking=second_booking)

        self.assertNotEqual(first_ticket.ticket_code, second_ticket.ticket_code)
        self.assertTrue(bool(first_ticket.qr_code))
        self.assertTrue(bool(second_ticket.qr_code))

    def test_admin_offline_booking_confirms_walk_in_immediately(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse('offline_booking'),
            {
                'username': 'Walk In',
                'user_email': 'walkin@example.com',
                'event': str(self.event.id),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(pk=response.data['booking']['id'])
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(booking.booking_source, Booking.SOURCE_OFFLINE)
        self.assertEqual(booking.payments.first().provider, Payment.PROVIDER_CASH)
        self.assertTrue(hasattr(booking, 'ticket'))

    def test_ticket_scan_allows_event_organizer_and_blocks_duplicate_scan(self):
        booking = Booking.objects.create(
            user=self.attendee,
            event=self.event,
            status=Booking.STATUS_CONFIRMED,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('50.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('50.00'),
            confirmed_at=timezone.now(),
        )
        ticket = Ticket.objects.create(booking=booking)

        self.client.force_authenticate(user=self.organizer)
        first_response = self.client.post(
            reverse('ticket_scan'),
            {
                'ticket_code': ticket.ticket_code,
                'mark_checked_in': True,
            },
            format='json',
        )
        second_response = self.client.post(
            reverse('ticket_scan'),
            {
                'ticket_code': ticket.ticket_code,
                'mark_checked_in': True,
            },
            format='json',
        )

        ticket.refresh_from_db()

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertTrue(ticket.is_scanned)
        self.assertEqual(second_response.status_code, status.HTTP_409_CONFLICT)
