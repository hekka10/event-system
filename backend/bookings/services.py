import logging
import base64
import binascii
import hashlib
import hmac
import json
import ssl
import uuid
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone

from events.models import Event
from users.models import StudentVerification

from .models import Booking, Payment


logger = logging.getLogger(__name__)


User = get_user_model()
TWO_DECIMAL_PLACES = Decimal('0.01')


def quantize_amount(amount):
    return Decimal(amount).quantize(TWO_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


def get_student_discount_rate():
    percentage = Decimal(str(getattr(settings, 'STUDENT_DISCOUNT_PERCENT', 20)))
    return percentage / Decimal('100')


def get_verified_student_record(user):
    verification = getattr(user, 'student_verification', None)
    if verification and verification.status == StudentVerification.STATUS_APPROVED:
        return verification

    return StudentVerification.objects.filter(
        user=user,
        status=StudentVerification.STATUS_APPROVED,
    ).first()


def get_booking_validation_error(user, event, booking_id_to_ignore=None):
    if event.date <= timezone.now():
        return {'event': 'Cannot book an event that is in the past.'}

    if not event.is_approved:
        return {'event': 'Cannot book an unapproved event.'}

    existing_booking = Booking.objects.filter(user=user, event=event).exclude(
        status__in=[Booking.STATUS_CANCELLED, Booking.STATUS_FAILED]
    )
    if booking_id_to_ignore:
        existing_booking = existing_booking.exclude(pk=booking_id_to_ignore)

    if existing_booking.exists():
        return {'non_field_errors': 'You have already booked this event.'}

    confirmed_bookings = Booking.objects.filter(
        event=event,
        status=Booking.STATUS_CONFIRMED,
    ).count()
    if confirmed_bookings >= event.capacity:
        return {'event': 'This event is already at full capacity.'}

    return None


def calculate_booking_pricing(user, event):
    base_price = quantize_amount(event.price or 0)
    verification = get_verified_student_record(user)
    is_student = verification is not None
    discount_amount = quantize_amount(base_price * get_student_discount_rate()) if is_student else Decimal('0.00')
    total_price = quantize_amount(max(base_price - discount_amount, Decimal('0.00')))

    return {
        'base_price': base_price,
        'discount_amount': discount_amount,
        'total_price': total_price,
        'is_student': is_student,
        'student_verification': verification,
    }


def create_pending_booking(user, event, booking_source=Booking.SOURCE_ONLINE):
    pricing = calculate_booking_pricing(user, event)
    booking = Booking.objects.create(
        user=user,
        event=event,
        status=Booking.STATUS_PENDING,
        booking_source=booking_source,
        is_student=pricing['is_student'],
        base_price=pricing['base_price'],
        discount_amount=pricing['discount_amount'],
        total_price=pricing['total_price'],
    )
    return booking


def build_capacity_failure_response(provider_response=None):
    payload = dict(provider_response or {})
    payload['reason'] = 'event_full'
    payload['message'] = 'This event is already at full capacity.'
    return payload


def build_payment_reference(prefix='PAY'):
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"


def build_checkout_url(payment):
    return build_absolute_frontend_url(f'/checkout/{payment.id}')


def build_booking_cancellation_response(provider_response=None):
    payload = dict(provider_response or {})
    payload['reason'] = 'booking_cancelled'
    payload['message'] = 'Booking was cancelled before payment confirmation.'
    return payload


def get_missing_esewa_settings():
    required_settings = [
        'ESEWA_PRODUCT_CODE',
        'ESEWA_SECRET_KEY',
        'ESEWA_FORM_URL',
        'ESEWA_STATUS_URL',
    ]
    return [
        setting_name
        for setting_name in required_settings
        if not str(getattr(settings, setting_name, '')).strip()
    ]


def get_online_payment_provider():
    provider = getattr(settings, 'PAYMENT_PROVIDER', Payment.PROVIDER_MOCK).upper()
    if provider == Payment.PROVIDER_ESEWA:
        missing_settings = get_missing_esewa_settings()
        if missing_settings:
            logger.warning(
                'PAYMENT_PROVIDER is ESEWA but missing config for %s. Falling back to MOCK.',
                ', '.join(missing_settings),
            )
            return Payment.PROVIDER_MOCK
        return Payment.PROVIDER_ESEWA
    return Payment.PROVIDER_MOCK


def build_absolute_frontend_url(path, query_params=None):
    base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:5173').rstrip('/')
    url = f"{base_url}{path}"
    if query_params:
        return f"{url}?{urlencode(query_params)}"
    return url


def build_frontend_payment_return_url(payment=None, payment_status='pending', gateway='esewa'):
    path = f"/checkout/{payment.id}" if payment is not None else '/my-bookings'
    return build_absolute_frontend_url(
        path,
        query_params={
            'gateway': gateway,
            'status': payment_status,
        },
    )


def build_absolute_backend_url(path, query_params=None):
    base_url = getattr(settings, 'BACKEND_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
    url = f"{base_url}{path}"
    if query_params:
        return f"{url}?{urlencode(query_params)}"
    return url


def get_esewa_success_url(payment=None):
    if payment is None:
        return build_absolute_backend_url('/api/payments/esewa/success/')
    return build_absolute_backend_url(f'/api/payments/esewa/success/{payment.id}/')


def get_esewa_failure_url(payment=None):
    if payment is None:
        return build_absolute_backend_url('/api/payments/esewa/failure/')
    return build_absolute_backend_url(f'/api/payments/esewa/failure/{payment.id}/')


def generate_esewa_signature(total_amount, transaction_uuid, product_code):
    secret_key = getattr(settings, 'ESEWA_SECRET_KEY', '')
    if not secret_key:
        raise ValueError('ESEWA_SECRET_KEY is not configured.')

    signed_payload = (
        f"total_amount={quantize_amount(total_amount)},"
        f"transaction_uuid={transaction_uuid},"
        f"product_code={product_code}"
    )
    digest = hmac.new(
        secret_key.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode('utf-8')


def build_esewa_payload(payment):
    product_code = getattr(settings, 'ESEWA_PRODUCT_CODE', '')
    if not product_code:
        raise ValueError('ESEWA_PRODUCT_CODE is not configured.')

    total_amount = quantize_amount(payment.amount)
    transaction_uuid = str(payment.id)

    return {
        'amount': str(total_amount),
        'tax_amount': '0',
        'total_amount': str(total_amount),
        'transaction_uuid': transaction_uuid,
        'product_code': product_code,
        'product_service_charge': '0',
        'product_delivery_charge': '0',
        'success_url': get_esewa_success_url(payment),
        'failure_url': get_esewa_failure_url(payment),
        'signed_field_names': 'total_amount,transaction_uuid,product_code',
        'signature': generate_esewa_signature(
            total_amount=total_amount,
            transaction_uuid=transaction_uuid,
            product_code=product_code,
        ),
    }


def decode_esewa_callback_data(raw_value):
    if not raw_value:
        return {}

    encoded_value = str(raw_value).strip()
    encoded_value += '=' * (-len(encoded_value) % 4)

    try:
        decoded_value = base64.b64decode(encoded_value)
        payload = json.loads(decoded_value.decode('utf-8'))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {}

    return payload if isinstance(payload, dict) else {}


def get_esewa_provider_reference(callback_payload=None, verification_payload=None):
    callback_payload = callback_payload or {}
    verification_payload = verification_payload or {}
    return (
        verification_payload.get('transaction_code')
        or callback_payload.get('transaction_code')
        or callback_payload.get('reference_id')
        or callback_payload.get('ref_id')
        or ''
    )


def is_esewa_verification_complete(verification_payload):
    return str((verification_payload or {}).get('status', '')).upper() == 'COMPLETE'


def attach_esewa_checkout_details(payment):
    payment.checkout_url = getattr(settings, 'ESEWA_FORM_URL', '').strip()
    payment.provider_response = {
        **(payment.provider_response or {}),
        'form_fields': build_esewa_payload(payment),
    }
    payment.save(update_fields=['checkout_url', 'provider_response', 'updated_at'])
    return payment


@transaction.atomic
def create_replacement_payment(payment):
    locked_payment = Payment.objects.select_for_update().select_related('booking', 'user').get(pk=payment.pk)
    booking = locked_payment.booking

    if locked_payment.status == Payment.STATUS_SUCCESS or booking.status == Booking.STATUS_CONFIRMED:
        raise ValueError('A successful payment already exists for this booking.')

    if booking.status != Booking.STATUS_PENDING:
        raise ValueError('Only pending bookings can start a new payment session.')

    if locked_payment.status != Payment.STATUS_FAILED:
        provider_response = {
            **(locked_payment.provider_response or {}),
            'reason': 'superseded',
            'message': 'Payment replaced with a fresh checkout session.',
        }
        locked_payment.status = Payment.STATUS_FAILED
        locked_payment.provider_response = provider_response
        locked_payment.verified_at = timezone.now()
        locked_payment.save(
            update_fields=['status', 'provider_response', 'verified_at', 'updated_at']
        )

    provider = locked_payment.provider
    if provider == Payment.PROVIDER_ESEWA:
        provider = get_online_payment_provider()

    return create_payment_for_booking(
        booking,
        provider=provider,
        method=locked_payment.method or 'ONLINE',
    )


def verify_esewa_payment(payment):
    status_url = getattr(settings, 'ESEWA_STATUS_URL', '').strip()
    product_code = getattr(settings, 'ESEWA_PRODUCT_CODE', '').strip()
    verify_ssl = getattr(settings, 'ESEWA_VERIFY_SSL', True)

    if not status_url:
        raise ValueError('ESEWA_STATUS_URL is not configured.')
    if not product_code:
        raise ValueError('ESEWA_PRODUCT_CODE is not configured.')

    query = urlencode(
        {
            'product_code': product_code,
            'total_amount': str(quantize_amount(payment.amount)),
            'transaction_uuid': str(payment.id),
        }
    )

    ssl_context = None
    if not verify_ssl:
        ssl_context = ssl._create_unverified_context()

    with urlopen(f"{status_url}?{query}", timeout=15, context=ssl_context) as response:
        return json.loads(response.read().decode('utf-8'))


@transaction.atomic
def create_payment_for_booking(booking, provider=Payment.PROVIDER_MOCK, method='ONLINE', status=Payment.STATUS_INITIATED):
    payment = Payment.objects.create(
        booking=booking,
        user=booking.user,
        provider=provider,
        method=method,
        status=status,
        amount=booking.total_price,
        external_reference=build_payment_reference(),
        checkout_url='',
    )

    if provider == Payment.PROVIDER_MOCK:
        payment.checkout_url = build_checkout_url(payment)
        payment.save(update_fields=['checkout_url', 'updated_at'])
    elif provider == Payment.PROVIDER_ESEWA:
        payment.currency = 'NPR'
        payment.save(update_fields=['currency', 'updated_at'])
        payment = attach_esewa_checkout_details(payment)

    return payment


@transaction.atomic
def process_successful_payment(payment, provider_reference='', provider_response=None):
    locked_payment = Payment.objects.select_for_update().select_related('booking').get(pk=payment.pk)
    booking = locked_payment.booking
    event = Event.objects.select_for_update().get(pk=booking.event_id)

    if booking.status == Booking.STATUS_CANCELLED:
        if locked_payment.status != Payment.STATUS_SUCCESS:
            locked_payment.status = Payment.STATUS_FAILED
            locked_payment.provider_reference = (
                provider_reference
                or locked_payment.provider_reference
                or locked_payment.external_reference
            )
            locked_payment.provider_response = build_booking_cancellation_response(provider_response)
            locked_payment.verified_at = timezone.now()
            locked_payment.save(
                update_fields=[
                    'status',
                    'provider_reference',
                    'provider_response',
                    'verified_at',
                    'updated_at',
                ]
            )

        return locked_payment, getattr(booking, 'ticket', None), (
            'This booking has been cancelled and can no longer be confirmed.'
        )

    confirmed_count = Booking.objects.filter(
        event_id=event.id,
        status=Booking.STATUS_CONFIRMED,
    ).exclude(pk=booking.pk).count()

    if confirmed_count >= event.capacity and booking.status != Booking.STATUS_CONFIRMED:
        if locked_payment.status != Payment.STATUS_FAILED:
            locked_payment.status = Payment.STATUS_FAILED
            locked_payment.provider_reference = (
                provider_reference
                or locked_payment.provider_reference
                or locked_payment.external_reference
            )
            locked_payment.provider_response = build_capacity_failure_response(provider_response)
            locked_payment.verified_at = timezone.now()
            locked_payment.save(
                update_fields=[
                    'status',
                    'provider_reference',
                    'provider_response',
                    'verified_at',
                    'updated_at',
                ]
            )

        booking.mark_failed()
        return locked_payment, None, 'This event is already at full capacity.'

    if locked_payment.status != Payment.STATUS_SUCCESS:
        locked_payment.status = Payment.STATUS_SUCCESS
        locked_payment.provider_reference = provider_reference or locked_payment.provider_reference or locked_payment.external_reference
        locked_payment.provider_response = provider_response or locked_payment.provider_response
        locked_payment.paid_at = locked_payment.paid_at or timezone.now()
        locked_payment.verified_at = timezone.now()
        locked_payment.save(
            update_fields=[
                'status',
                'provider_reference',
                'provider_response',
                'paid_at',
                'verified_at',
                'updated_at',
            ]
        )

    ticket = booking.confirm()
    return locked_payment, ticket, None


@transaction.atomic
def process_failed_payment(payment, provider_reference='', provider_response=None):
    locked_payment = Payment.objects.select_for_update().select_related('booking').get(pk=payment.pk)

    if locked_payment.status != Payment.STATUS_FAILED:
        locked_payment.status = Payment.STATUS_FAILED
        locked_payment.provider_reference = provider_reference or locked_payment.provider_reference
        locked_payment.provider_response = provider_response or locked_payment.provider_response
        locked_payment.verified_at = timezone.now()
        locked_payment.save(
            update_fields=[
                'status',
                'provider_reference',
                'provider_response',
                'verified_at',
                'updated_at',
            ]
        )

    locked_payment.booking.mark_failed()
    return locked_payment


def build_unique_username(seed):
    base = ''.join(ch for ch in seed.lower() if ch.isalnum()) or 'guest'
    candidate = base[:150]
    suffix = 1

    while User.objects.filter(username=candidate).exists():
        trimmed_base = base[: max(1, 150 - len(str(suffix)) - 1)]
        candidate = f"{trimmed_base}{suffix}"
        suffix += 1

    return candidate


def get_or_create_offline_user(email, username=''):
    normalized_email = email.strip().lower()
    user = User.objects.filter(email=normalized_email).first()
    if user:
        return user, False

    user = User(
        email=normalized_email,
        username=build_unique_username(username or normalized_email.split('@')[0]),
    )
    user.set_unusable_password()
    user.save()
    return user, True


def send_booking_confirmation_email(booking, ticket=None, fail_silently=True):
    ticket = ticket or getattr(booking, 'ticket', None)
    if ticket is None:
        ticket = booking.ticket

    qr_name = ticket.qr_code.name if ticket.qr_code else ''
    if not qr_name or not ticket.qr_code.storage.exists(qr_name):
        if qr_name:
            logger.warning(
                "QR code file missing for ticket %s; regenerating before email send.",
                ticket.ticket_code,
            )
        ticket.generate_qr()
        ticket.save(update_fields=['qr_code'])

    frontend_base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:5173').rstrip('/')
    booking_url = f"{frontend_base_url}/my-bookings"
    subject = f"Booking Confirmation - {booking.event.title}"
    text_body = (
        f"Hello {booking.user.username or booking.user.email},\n\n"
        f"Your booking for {booking.event.title} is confirmed.\n"
        f"Ticket Code: {ticket.ticket_code}\n"
        f"Date: {booking.event.date}\n"
        f"Location: {booking.event.location}\n"
        f"Amount Paid: NRs {booking.total_price}\n\n"
        f"You can view your booking at {booking_url}\n"
    )
    html_body = f"""
        <p>Hello {booking.user.username or booking.user.email},</p>
        <p>Your booking for <strong>{booking.event.title}</strong> is confirmed.</p>
        <ul>
            <li><strong>Ticket Code:</strong> {ticket.ticket_code}</li>
            <li><strong>Date:</strong> {booking.event.date}</li>
            <li><strong>Location:</strong> {booking.event.location}</li>
            <li><strong>Amount Paid:</strong> NRs {booking.total_price}</li>
        </ul>
        <p>Your QR ticket is attached to this email.</p>
        <p><a href="{booking_url}">Open my bookings</a></p>
    """

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.user.email],
    )
    email.attach_alternative(html_body, "text/html")

    if ticket.qr_code:
        ticket.qr_code.open('rb')
        try:
            email.attach(
                filename=f"{ticket.ticket_code}.png",
                content=ticket.qr_code.read(),
                mimetype='image/png',
            )
        finally:
            ticket.qr_code.close()

    try:
        email.send(fail_silently=fail_silently)
    except Exception:
        logger.exception("Failed to send booking confirmation email for booking %s", booking.id)
        raise
