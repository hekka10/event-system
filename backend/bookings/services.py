from decimal import Decimal, ROUND_HALF_UP
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone

from events.models import Event
from users.models import StudentVerification

from .models import Booking, Payment


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
    base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:5173').rstrip('/')
    return f"{base_url}/checkout/{payment.id}"


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

    return payment


@transaction.atomic
def process_successful_payment(payment, provider_reference='', provider_response=None):
    locked_payment = Payment.objects.select_for_update().select_related('booking').get(pk=payment.pk)
    booking = locked_payment.booking
    event = Event.objects.select_for_update().get(pk=booking.event_id)

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


def send_booking_confirmation_email(booking, ticket=None):
    ticket = ticket or getattr(booking, 'ticket', None)
    if ticket is None:
        ticket = booking.ticket

    frontend_base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:5173').rstrip('/')
    booking_url = f"{frontend_base_url}/my-bookings"
    subject = f"Booking Confirmation - {booking.event.title}"
    text_body = (
        f"Hello {booking.user.username or booking.user.email},\n\n"
        f"Your booking for {booking.event.title} is confirmed.\n"
        f"Ticket Code: {ticket.ticket_code}\n"
        f"Date: {booking.event.date}\n"
        f"Location: {booking.event.location}\n"
        f"Amount Paid: ${booking.total_price}\n\n"
        f"You can view your booking at {booking_url}\n"
    )
    html_body = f"""
        <p>Hello {booking.user.username or booking.user.email},</p>
        <p>Your booking for <strong>{booking.event.title}</strong> is confirmed.</p>
        <ul>
            <li><strong>Ticket Code:</strong> {ticket.ticket_code}</li>
            <li><strong>Date:</strong> {booking.event.date}</li>
            <li><strong>Location:</strong> {booking.event.location}</li>
            <li><strong>Amount Paid:</strong> ${booking.total_price}</li>
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

    email.send(fail_silently=True)
