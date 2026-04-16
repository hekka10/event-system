import base64
import json
import os
import tempfile
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from events.models import Category, Event

from .models import Booking, Payment, Ticket
from .services import build_esewa_payload, generate_esewa_signature, verify_esewa_payment


User = get_user_model()


@override_settings(PAYMENT_PROVIDER='MOCK')
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

    def test_pending_booking_can_be_cancelled(self):
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
        response = self.client.post(
            reverse('booking-cancel', args=[booking.id]),
            format='json',
        )

        booking.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(booking.status, Booking.STATUS_CANCELLED)
        self.assertEqual(response.data['booking']['status'], Booking.STATUS_CANCELLED)
        self.assertFalse(response.data['booking']['can_cancel'])

    def test_confirmed_future_booking_can_be_cancelled(self):
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
        Ticket.objects.create(booking=booking)

        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(
            reverse('booking-cancel', args=[booking.id]),
            format='json',
        )

        booking.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(booking.status, Booking.STATUS_CANCELLED)
        self.assertTrue(Ticket.objects.filter(booking=booking).exists())

    def test_past_booking_cannot_be_cancelled(self):
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
        Event.objects.filter(pk=self.event.pk).update(date=timezone.now() - timedelta(hours=1))

        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(
            reverse('booking-cancel', args=[booking.id]),
            format='json',
        )

        booking.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Past events cannot be cancelled', str(response.data['detail']))
        self.assertEqual(booking.status, Booking.STATUS_PENDING)

    def test_checked_in_booking_cannot_be_cancelled(self):
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
        ticket.is_scanned = True
        ticket.scanned_at = timezone.now()
        ticket.checked_in_by = self.organizer
        ticket.save(update_fields=['is_scanned', 'scanned_at', 'checked_in_by'])

        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(
            reverse('booking-cancel', args=[booking.id]),
            format='json',
        )

        booking.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Checked-in bookings cannot be cancelled', str(response.data['detail']))
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='no-reply@test.com',
    )
    def test_confirmed_booking_can_resend_ticket_email(self):
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
        mail.outbox = []

        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(
            reverse('booking-send-ticket-email', args=[booking.id]),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.attendee.email)
        self.assertEqual(response.data['ticket_code'], ticket.ticket_code)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.attendee.email])
        self.assertEqual(len(mail.outbox[0].attachments), 1)

    def test_confirmed_booking_resend_ticket_email_regenerates_missing_qr_file(self):
        with tempfile.TemporaryDirectory() as media_root:
            with self.settings(
                EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                DEFAULT_FROM_EMAIL='no-reply@test.com',
                MEDIA_ROOT=media_root,
            ):
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
                missing_qr_name = ticket.qr_code.name

                os.remove(ticket.qr_code.path)
                self.assertFalse(ticket.qr_code.storage.exists(missing_qr_name))

                mail.outbox = []
                self.client.force_authenticate(user=self.attendee)
                response = self.client.post(
                    reverse('booking-send-ticket-email', args=[booking.id]),
                    format='json',
                )

                ticket.refresh_from_db()

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(ticket.qr_code.storage.exists(ticket.qr_code.name))
                self.assertEqual(ticket.qr_code.name, missing_qr_name)
                self.assertEqual(len(mail.outbox), 1)
                self.assertEqual(len(mail.outbox[0].attachments), 1)

    def test_pending_booking_cannot_resend_ticket_email(self):
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
        response = self.client.post(
            reverse('booking-send-ticket-email', args=[booking.id]),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only confirmed bookings', str(response.data))

    def test_cancelling_pending_booking_blocks_late_payment_confirmation(self):
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
            external_reference='PAY-CANCELLED-LATE',
        )

        self.client.force_authenticate(user=self.attendee)
        cancel_response = self.client.post(
            reverse('booking-cancel', args=[booking.id]),
            format='json',
        )
        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse('payment_verify', args=[payment.id]),
            {
                'status': Payment.STATUS_SUCCESS,
                'provider_reference': 'SANDBOX-LATE',
                'provider_response': {'gateway': 'sandbox'},
            },
            format='json',
        )

        booking.refresh_from_db()
        payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('cancelled', str(response.data['detail']).lower())
        self.assertEqual(booking.status, Booking.STATUS_CANCELLED)
        self.assertEqual(payment.status, Payment.STATUS_FAILED)

    def test_cancelled_ticket_cannot_be_scanned(self):
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

        self.client.force_authenticate(user=self.attendee)
        cancel_response = self.client.post(
            reverse('booking-cancel', args=[booking.id]),
            format='json',
        )
        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(
            reverse('ticket_scan'),
            {
                'ticket_code': ticket.ticket_code,
                'event': str(self.event.id),
            },
            format='json',
        )

        ticket.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('no longer active', str(response.data['detail']).lower())
        self.assertFalse(ticket.is_scanned)

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
        booking = Booking.objects.first()
        self.assertFalse(Ticket.objects.filter(booking=booking).exists())

    @override_settings(
        PAYMENT_PROVIDER='ESEWA',
        ESEWA_PRODUCT_CODE='',
        ESEWA_SECRET_KEY='',
        ESEWA_FORM_URL='',
        ESEWA_STATUS_URL='',
    )
    def test_payment_initiation_falls_back_to_mock_when_esewa_config_is_missing(self):
        self.client.force_authenticate(user=self.attendee)

        response = self.client.post(
            reverse('payment_initiate'),
            {'event': str(self.event.id)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['next_action'], 'COMPLETE_PAYMENT')
        self.assertEqual(response.data['payment']['provider'], Payment.PROVIDER_MOCK)
        self.assertTrue(response.data['payment']['checkout_url'].endswith(f"/checkout/{response.data['payment']['id']}"))

    @override_settings(
        PAYMENT_PROVIDER='ESEWA',
        ESEWA_PRODUCT_CODE='EPAYTEST',
        ESEWA_SECRET_KEY='8gBm/:&EnhH.1/q',
        ESEWA_FORM_URL='https://rc-epay.esewa.com.np/api/epay/main/v2/form',
        ESEWA_STATUS_URL='https://rc.esewa.com.np/api/epay/transaction/status/',
        BACKEND_BASE_URL='http://127.0.0.1:8000',
    )
    def test_payment_initiation_returns_esewa_checkout_payload_when_enabled(self):
        self.client.force_authenticate(user=self.attendee)

        response = self.client.post(
            reverse('payment_initiate'),
            {'event': str(self.event.id)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['next_action'], 'REDIRECT_TO_ESEWA')
        self.assertEqual(response.data['payment']['provider'], Payment.PROVIDER_ESEWA)
        self.assertEqual(response.data['payment']['currency'], 'NPR')
        self.assertEqual(
            response.data['payment']['checkout_url'],
            'https://rc-epay.esewa.com.np/api/epay/main/v2/form',
        )
        self.assertIsNotNone(response.data['payment']['form_fields'])
        self.assertEqual(
            response.data['payment']['form_fields']['transaction_uuid'],
            response.data['payment']['id'],
        )

    def test_payments_initiate_endpoint_alias_creates_pending_payment(self):
        self.client.force_authenticate(user=self.attendee)

        response = self.client.post(
            reverse('payments_initiate'),
            {'event': str(self.event.id)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['next_action'], 'COMPLETE_PAYMENT')
        self.assertIn('transaction_ref', response.data['payment'])
        self.assertEqual(response.data['payment']['transaction_ref'], response.data['payment']['external_reference'])

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
        self.assertEqual(response.data['next_action'], 'BOOKING_CONFIRMED')
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(payment.status, Payment.STATUS_SUCCESS)
        ticket = Ticket.objects.get(booking=booking)
        self.assertTrue(ticket.ticket_code.startswith('TICKET-'))
        self.assertTrue(bool(ticket.qr_code))
        self.assertIn('qr_code_url', response.data['booking']['ticket'])
        self.assertEqual(response.data['ticket_code'], ticket.ticket_code)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].attachments)

    @override_settings(
        PAYMENT_PROVIDER='ESEWA',
        ESEWA_PRODUCT_CODE='EPAYTEST',
        ESEWA_SECRET_KEY='8gBm/:&EnhH.1/q',
        ESEWA_FORM_URL='https://rc-epay.esewa.com.np/api/epay/main/v2/form',
        ESEWA_STATUS_URL='https://rc.esewa.com.np/api/epay/transaction/status/',
        BACKEND_BASE_URL='http://127.0.0.1:8000',
    )
    def test_payments_retry_creates_fresh_esewa_session(self):
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
            provider=Payment.PROVIDER_ESEWA,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('50.00'),
            currency='NPR',
            external_reference='PAY-ESEWA-OLD',
        )

        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(
            reverse('payments_retry', args=[payment.id]),
            format='json',
        )

        payment.refresh_from_db()
        booking.refresh_from_db()
        new_payment = Payment.objects.exclude(pk=payment.id).get(booking=booking)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['next_action'], 'REDIRECT_TO_ESEWA')
        self.assertEqual(payment.status, Payment.STATUS_FAILED)
        self.assertEqual(booking.status, Booking.STATUS_PENDING)
        self.assertEqual(new_payment.provider, Payment.PROVIDER_ESEWA)
        self.assertNotEqual(str(new_payment.id), str(payment.id))
        self.assertEqual(response.data['payment']['id'], str(new_payment.id))

    @override_settings(FRONTEND_BASE_URL='http://localhost:5173')
    @patch('bookings.views.verify_esewa_payment')
    def test_esewa_success_callback_confirms_booking_and_redirects_to_checkout(self, mock_verify_esewa_payment):
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
            provider=Payment.PROVIDER_ESEWA,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('50.00'),
            currency='NPR',
            external_reference='PAY-ESEWA-CALLBACK-SUCCESS',
        )
        mock_verify_esewa_payment.return_value = {
            'status': 'COMPLETE',
            'transaction_code': 'ESEWA-TXN-123',
        }
        callback_payload = base64.b64encode(
            json.dumps({'transaction_uuid': str(payment.id)}).encode('utf-8')
        ).decode('utf-8')

        response = self.client.get(
            reverse('esewa_success', args=[payment.id]),
            {
                'data': callback_payload,
            },
        )

        booking.refresh_from_db()
        payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response['Location'],
            f'http://localhost:5173/checkout/{payment.id}?gateway=esewa&status=success',
        )
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(payment.provider_reference, 'ESEWA-TXN-123')
        self.assertTrue(Ticket.objects.filter(booking=booking).exists())

    @override_settings(FRONTEND_BASE_URL='http://localhost:5173')
    def test_esewa_failure_callback_marks_payment_failed_and_redirects_to_checkout(self):
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
            provider=Payment.PROVIDER_ESEWA,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('50.00'),
            currency='NPR',
            external_reference='PAY-ESEWA-CALLBACK-FAIL',
        )

        response = self.client.get(
            reverse('esewa_failure', args=[payment.id]),
        )

        booking.refresh_from_db()
        payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response['Location'],
            f'http://localhost:5173/checkout/{payment.id}?gateway=esewa&status=failed',
        )
        self.assertEqual(booking.status, Booking.STATUS_FAILED)
        self.assertEqual(payment.status, Payment.STATUS_FAILED)

    @override_settings(FRONTEND_BASE_URL='http://localhost:5173')
    @patch('bookings.views.verify_esewa_payment')
    def test_esewa_success_callback_recovers_legacy_query_string_format(self, mock_verify_esewa_payment):
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
            provider=Payment.PROVIDER_ESEWA,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('50.00'),
            currency='NPR',
            external_reference='PAY-ESEWA-LEGACY-CALLBACK',
        )
        mock_verify_esewa_payment.return_value = {
            'status': 'COMPLETE',
            'transaction_code': 'ESEWA-TXN-LEGACY',
        }
        callback_payload = base64.b64encode(
            json.dumps({'transaction_uuid': str(payment.id)}).encode('utf-8')
        ).decode('utf-8')

        response = self.client.get(
            reverse('esewa_success_legacy'),
            {
                'payment_id': f'{payment.id}?data={callback_payload}',
            },
        )

        booking.refresh_from_db()
        payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(payment.status, Payment.STATUS_SUCCESS)

    def test_booking_confirm_raises_without_successful_payment(self):
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
        Payment.objects.create(
            booking=booking,
            user=self.attendee,
            provider=Payment.PROVIDER_MOCK,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('50.00'),
            external_reference='PAY-NOT-SUCCESSFUL',
            checkout_url='http://localhost:5173/checkout/test',
        )

        with self.assertRaises(ValidationError):
            booking.confirm()

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_PENDING)
        self.assertFalse(Ticket.objects.filter(booking=booking).exists())

    def test_payments_verify_endpoint_accepts_transaction_reference(self):
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
            external_reference='PAY-VERIFY-BY-REF',
            checkout_url='http://localhost:5173/checkout/test',
        )

        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(
            reverse('payments_verify'),
            {
                'transaction_ref': payment.external_reference,
                'status': Payment.STATUS_SUCCESS,
                'provider_reference': 'SANDBOX-REF-123',
            },
            format='json',
        )

        booking.refresh_from_db()
        payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(response.data['payment']['transaction_ref'], payment.external_reference)

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
        self.assertEqual(response.data['attendee_email'], 'walkin@example.com')
        self.assertTrue(response.data['created_user'])

    def test_admin_offline_booking_alias_confirms_walk_in_immediately(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse('admin_offline_booking'),
            {
                'username': 'Walk In Alias',
                'user_email': 'aliaswalkin@example.com',
                'event': str(self.event.id),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(pk=response.data['booking']['id'])
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(response.data['ticket_code'], booking.ticket.ticket_code)

    def test_non_admin_cannot_create_offline_booking(self):
        self.client.force_authenticate(user=self.attendee)

        response = self.client.post(
            reverse('admin_offline_booking'),
            {
                'username': 'Walk In',
                'user_email': 'forbidden@example.com',
                'event': str(self.event.id),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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


class EsewaServiceTests(APITestCase):
    @override_settings(
        ESEWA_PRODUCT_CODE='EPAYTEST',
        ESEWA_SECRET_KEY='8gBm/:&EnhH.1/q',
        BACKEND_BASE_URL='http://127.0.0.1:8000',
        ESEWA_STATUS_URL='https://rc.esewa.com.np/api/epay/transaction/status/',
    )
    def test_build_esewa_payload_contains_signed_fields(self):
        user = User.objects.create_user(
            email='esewa@example.com',
            username='esewauser',
            password='password123',
        )
        category = Category.objects.create(name='Concert')
        event = Event.objects.create(
            title='eSewa Test Event',
            description='Concert',
            date=timezone.now() + timedelta(days=5),
            location='Arena',
            category=category,
            price=Decimal('100.00'),
            capacity=50,
            organizer=user,
            is_approved=True,
        )
        booking = Booking.objects.create(
            user=user,
            event=event,
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('100.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('100.00'),
        )
        payment = Payment.objects.create(
            booking=booking,
            user=user,
            provider=Payment.PROVIDER_ESEWA,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('100.00'),
            currency='NPR',
            external_reference='PAY-ESEWA-TEST',
        )

        payload = build_esewa_payload(payment)

        self.assertEqual(payload['product_code'], 'EPAYTEST')
        self.assertEqual(payload['transaction_uuid'], str(payment.id))
        self.assertEqual(payload['total_amount'], '100.00')
        self.assertEqual(payload['signed_field_names'], 'total_amount,transaction_uuid,product_code')
        self.assertEqual(
            payload['signature'],
            generate_esewa_signature('100.00', str(payment.id), 'EPAYTEST'),
        )
        self.assertEqual(
            payload['success_url'],
            f'http://127.0.0.1:8000/api/payments/esewa/success/{payment.id}/',
        )
        self.assertEqual(
            payload['failure_url'],
            f'http://127.0.0.1:8000/api/payments/esewa/failure/{payment.id}/',
        )

    @override_settings(
        ESEWA_PRODUCT_CODE='EPAYTEST',
        ESEWA_STATUS_URL='https://rc.esewa.com.np/api/epay/transaction/status/',
    )
    @patch('bookings.services.urlopen')
    def test_verify_esewa_payment_calls_status_api(self, mock_urlopen):
        user = User.objects.create_user(
            email='verify@example.com',
            username='verifyuser',
            password='password123',
        )
        category = Category.objects.create(name='Workshop')
        event = Event.objects.create(
            title='Verify Event',
            description='Workshop',
            date=timezone.now() + timedelta(days=4),
            location='Lab',
            category=category,
            price=Decimal('80.00'),
            capacity=40,
            organizer=user,
            is_approved=True,
        )
        booking = Booking.objects.create(
            user=user,
            event=event,
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('80.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('80.00'),
        )
        payment = Payment.objects.create(
            booking=booking,
            user=user,
            provider=Payment.PROVIDER_ESEWA,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('80.00'),
            currency='NPR',
            external_reference='PAY-ESEWA-VERIFY',
        )

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"status":"COMPLETE","total_amount":"80.00"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        payload = verify_esewa_payment(payment)

        self.assertEqual(payload['status'], 'COMPLETE')
        requested_url = mock_urlopen.call_args.args[0]
        self.assertIn('product_code=EPAYTEST', requested_url)
        self.assertIn(f'transaction_uuid={payment.id}', requested_url)
        self.assertIn('total_amount=80.00', requested_url)

    @override_settings(
        ESEWA_PRODUCT_CODE='EPAYTEST',
        ESEWA_STATUS_URL='https://rc.esewa.com.np/api/epay/transaction/status/',
        ESEWA_VERIFY_SSL=False,
    )
    @patch('bookings.services.urlopen')
    def test_verify_esewa_payment_uses_unverified_context_when_ssl_checks_are_disabled(self, mock_urlopen):
        user = User.objects.create_user(
            email='sslverify@example.com',
            username='sslverify',
            password='password123',
        )
        category = Category.objects.create(name='Talk')
        event = Event.objects.create(
            title='SSL Verify Event',
            description='Talk',
            date=timezone.now() + timedelta(days=4),
            location='Hall',
            category=category,
            price=Decimal('10.00'),
            capacity=20,
            organizer=user,
            is_approved=True,
        )
        booking = Booking.objects.create(
            user=user,
            event=event,
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('10.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('10.00'),
        )
        payment = Payment.objects.create(
            booking=booking,
            user=user,
            provider=Payment.PROVIDER_ESEWA,
            method='ONLINE',
            status=Payment.STATUS_INITIATED,
            amount=Decimal('10.00'),
            currency='NPR',
            external_reference='PAY-ESEWA-SSL-CONTEXT',
        )

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"status":"COMPLETE","total_amount":"10.00"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        verify_esewa_payment(payment)

        self.assertIsNotNone(mock_urlopen.call_args.kwargs['context'])
