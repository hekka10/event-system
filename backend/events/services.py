from django.db.models import Case, Count, F, IntegerField, Q, Value, When
from django.utils import timezone

from bookings.models import Booking

from .models import Event


DEFAULT_RECOMMENDATION_LIMIT = 6


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
