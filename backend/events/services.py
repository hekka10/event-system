from datetime import timedelta
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models import Case, Count, F, IntegerField, Q, Value, When
from django.utils import timezone

from bookings.models import Booking

from .models import Event


DEFAULT_RECOMMENDATION_LIMIT = 6
DEFAULT_EVENT_REMINDER_LEAD_HOURS = 12
logger = logging.getLogger(__name__)


def get_recommended_events_for_user(user, limit=DEFAULT_RECOMMENDATION_LIMIT):
    """
    Recommend upcoming events using the user's confirmed past bookings.

    The rule-based strategy is:
    1. Find categories from events the user has already attended.
    2. Recommend upcoming approved events in those categories first.
    3. Exclude events already booked by the user and sold-out events.
    4. Fill any remaining slots with popular upcoming fallback events.
    """
    now = timezone.now()
    active_booked_event_ids = Booking.objects.filter(user=user).exclude(
        status__in=[Booking.STATUS_CANCELLED, Booking.STATUS_FAILED]
    ).values_list('event_id', flat=True)

    base_queryset = Event.objects.select_related('category', 'organizer').annotate(
        confirmed_booking_count_value=Count(
            'bookings',
            filter=Q(bookings__status=Booking.STATUS_CONFIRMED),
            distinct=True,
        )
    ).filter(
        date__gt=now,
        is_approved=True,
        confirmed_booking_count_value__lt=F('capacity'),
    ).exclude(
        id__in=active_booked_event_ids,
    )

    past_category_rows = (
        Booking.objects.filter(
            user=user,
            status=Booking.STATUS_CONFIRMED,
            event__date__lt=now,
        )
        .values('event__category')
        .annotate(total=Count('event__category'))
        .order_by('-total')
    )
    ordered_category_ids = [
        row['event__category']
        for row in past_category_rows
        if row['event__category'] is not None
    ]

    if not ordered_category_ids:
        return list(
            base_queryset.order_by(
                '-confirmed_booking_count_value',
                'date',
                '-created_at',
            )[:limit]
        )

    category_priority = Case(
        *[
            When(category_id=category_id, then=Value(index))
            for index, category_id in enumerate(ordered_category_ids)
        ],
        default=Value(len(ordered_category_ids)),
        output_field=IntegerField(),
    )

    personalized_events = list(
        base_queryset.filter(category_id__in=ordered_category_ids)
        .annotate(recommendation_priority=category_priority)
        .order_by(
            'recommendation_priority',
            '-confirmed_booking_count_value',
            'date',
            '-created_at',
        )[:limit]
    )

    if len(personalized_events) >= limit:
        return personalized_events

    fallback_events = list(
        base_queryset.exclude(id__in=[event.id for event in personalized_events]).order_by(
            '-confirmed_booking_count_value',
            'date',
            '-created_at',
        )[: limit - len(personalized_events)]
    )

    return personalized_events + fallback_events


def build_event_reminder_url():
    frontend_base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:5173').rstrip('/')
    return f"{frontend_base_url}/my-bookings"


def get_event_reminder_lead_time():
    hours = max(int(getattr(settings, 'EVENT_REMINDER_LEAD_HOURS', DEFAULT_EVENT_REMINDER_LEAD_HOURS)), 0)
    return timedelta(hours=hours)


def get_booking_ticket(booking):
    try:
        return booking.ticket
    except ObjectDoesNotExist:
        return None


def build_event_reminder_message(event, booking):
    manage_bookings_url = build_event_reminder_url()
    localized_event_date = timezone.localtime(event.date)
    formatted_event_date = localized_event_date.strftime('%A, %B %d, %Y at %I:%M %p %Z')
    ticket = get_booking_ticket(booking)
    attendee_name = (booking.user.username or '').strip() or booking.user.email
    ticket_line = f"Ticket code: {ticket.ticket_code}\n" if ticket else ''
    ticket_html = f"<p><strong>Ticket code:</strong> {ticket.ticket_code}</p>" if ticket else ""

    text_body = (
        f"Hello {attendee_name},\n\n"
        f"This is a reminder that {event.title} is coming up soon.\n\n"
        f"Date and time: {formatted_event_date}\n"
        f"Location: {event.location}\n"
        f"{ticket_line}"
        f"View your booking: {manage_bookings_url}\n\n"
        "We look forward to seeing you there.\n"
    )
    html_body = f"""
        <p>Hello {attendee_name},</p>
        <p>This is a reminder that <strong>{event.title}</strong> is coming up soon.</p>
        <p><strong>Date and time:</strong> {formatted_event_date}</p>
        <p><strong>Location:</strong> {event.location}</p>
        {ticket_html}
        <p><a href="{manage_bookings_url}">View your booking</a></p>
        <p>We look forward to seeing you there.</p>
    """

    email = EmailMultiAlternatives(
        subject=f"Reminder: {event.title}",
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.user.email],
    )
    email.attach_alternative(html_body, "text/html")
    return email


def build_event_reminder_messages(event, bookings):
    return [build_event_reminder_message(event, booking) for booking in bookings]


def send_event_reminder_emails(event, bookings, fail_silently=False):
    bookings = list(bookings)
    if not bookings:
        return {
            'sent_count': 0,
            'failed_count': 0,
            'failed_booking_ids': [],
        }

    connection = get_connection(fail_silently=fail_silently)
    sent_count = 0
    failed_booking_ids = []
    try:
        connection.open()
        for booking in bookings:
            message = build_event_reminder_message(event, booking)
            message.connection = connection
            try:
                sent = message.send(fail_silently=fail_silently) or 0
            except Exception:
                logger.exception(
                    "Failed to send reminder email for booking %s on event %s",
                    booking.id,
                    event.id,
                )
                failed_booking_ids.append(str(booking.id))
                continue

            if not sent:
                failed_booking_ids.append(str(booking.id))
                continue

            sent_count += sent
    except Exception:
        logger.exception("Failed to open reminder email connection for event %s", event.id)
        raise
    finally:
        connection.close()

    return {
        'sent_count': sent_count,
        'failed_count': len(failed_booking_ids),
        'failed_booking_ids': failed_booking_ids,
    }


def get_due_event_reminder_bookings(now=None, lead_time=None):
    now = now or timezone.now()
    lead_time = lead_time or get_event_reminder_lead_time()

    return Booking.objects.filter(
        status=Booking.STATUS_CONFIRMED,
        reminder_sent_at__isnull=True,
        event__date__gt=now,
        event__date__lte=now + lead_time,
    ).select_related(
        'user',
        'event',
        'ticket',
    ).order_by(
        'event__date',
        'confirmed_at',
        'created_at',
    )


def send_due_event_reminders(now=None, lead_time=None, fail_silently=False):
    due_bookings = list(get_due_event_reminder_bookings(now=now, lead_time=lead_time))
    if not due_bookings:
        return {
            'processed_count': 0,
            'sent_count': 0,
            'failed_count': 0,
            'sent_booking_ids': [],
            'failed_booking_ids': [],
        }

    connection = get_connection(fail_silently=fail_silently)
    sent_booking_ids = []
    failed_booking_ids = []

    try:
        connection.open()
        for booking in due_bookings:
            message = build_event_reminder_message(booking.event, booking)
            message.connection = connection

            try:
                sent = message.send(fail_silently=fail_silently) or 0
            except Exception:
                logger.exception(
                    "Failed to send automatic reminder email for booking %s",
                    booking.id,
                )
                failed_booking_ids.append(str(booking.id))
                continue

            if not sent:
                failed_booking_ids.append(str(booking.id))
                continue

            reminder_timestamp = timezone.now()
            Booking.objects.filter(
                pk=booking.pk,
                reminder_sent_at__isnull=True,
            ).update(
                reminder_sent_at=reminder_timestamp,
                updated_at=reminder_timestamp,
            )
            sent_booking_ids.append(str(booking.id))
    finally:
        connection.close()

    return {
        'processed_count': len(due_bookings),
        'sent_count': len(sent_booking_ids),
        'failed_count': len(failed_booking_ids),
        'sent_booking_ids': sent_booking_ids,
        'failed_booking_ids': failed_booking_ids,
    }
