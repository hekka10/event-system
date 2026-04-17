import csv

from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.decorators import action
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from bookings.models import Booking
from .models import Category, Event
from .permissions import IsAdminOrReadOnly, IsOrganizerOrAdmin
from .serializers import CategorySerializer, EventAttendeeSerializer, EventSerializer
from .services import get_recommended_events_for_user, send_event_reminder_emails


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related('category', 'organizer').annotate(
        confirmed_booking_count_value=Count(
            'bookings',
            filter=Q(bookings__status='CONFIRMED'),
            distinct=True,
        )
    ).order_by('date', '-created_at')
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOrganizerOrAdmin]

    def get_permissions(self):
        if self.action == 'approve':
            permission_classes = [permissions.IsAdminUser]
        elif self.action == 'attendees':
            permission_classes = [permissions.IsAuthenticated, IsOrganizerOrAdmin]
        elif self.action == 'send_reminder':
            permission_classes = [permissions.IsAuthenticated, IsOrganizerOrAdmin]
        elif self.action == 'recommended':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOrganizerOrAdmin]
        else:
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user, is_approved=False)

    def perform_update(self, serializer):
        serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset()

        # The public events page should only surface upcoming events.
        if self.action == 'list':
            queryset = queryset.filter(date__gt=timezone.now())
        
        # Admin can see all, regular users only see approved
        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.is_superuser)):
            if user.is_authenticated:
                queryset = queryset.filter(Q(is_approved=True) | Q(organizer=user))
            else:
                queryset = queryset.filter(is_approved=True)

        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        event = self.get_object()
        event.is_approved = True
        event.save(update_fields=['is_approved', 'updated_at'])
        serializer = self.get_serializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def recommended(self, request):
        recommended_events = get_recommended_events_for_user(request.user)
        serializer = self.get_serializer(recommended_events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='attendees')
    def attendees(self, request, pk=None):
        event = self.get_object()
        attendees = Booking.objects.filter(
            event=event,
            status=Booking.STATUS_CONFIRMED,
        ).select_related(
            'user',
            'ticket',
        ).order_by('confirmed_at', 'created_at')

        if request.query_params.get('export') == 'csv':
            return self._build_attendee_csv_response(event, attendees)

        summary = attendees.aggregate(
            confirmed_count=Count('id'),
            checked_in_count=Count('id', filter=Q(ticket__is_scanned=True)),
            student_count=Count('id', filter=Q(is_student=True)),
        )

        return Response(
            {
                'event': {
                    'id': str(event.id),
                    'title': event.title,
                },
                'summary': summary,
                'attendees': EventAttendeeSerializer(attendees, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def _build_attendee_csv_response(self, event, attendees):
        filename = f"{slugify(event.title) or 'event'}-attendees.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([
            'Booking ID',
            'Attendee Name',
            'Attendee Email',
            'Booking Source',
            'Student Ticket',
            'Total Paid',
            'Ticket Code',
            'Confirmed At',
            'Checked In',
            'Scanned At',
            'Booked At',
        ])

        for attendee in attendees:
            ticket = attendee.ticket if hasattr(attendee, 'ticket') else None
            writer.writerow([
                attendee.id,
                attendee.user.username or attendee.user.email,
                attendee.user.email,
                attendee.booking_source,
                'Yes' if attendee.is_student else 'No',
                attendee.total_price,
                ticket.ticket_code if ticket else '',
                attendee.confirmed_at.isoformat() if attendee.confirmed_at else '',
                'Yes' if ticket and ticket.is_scanned else 'No',
                ticket.scanned_at.isoformat() if ticket and ticket.scanned_at else '',
                attendee.created_at.isoformat() if attendee.created_at else '',
            ])

        return response

    @action(detail=True, methods=['post'], url_path='send-reminder')
    def send_reminder(self, request, pk=None):
        event = self.get_object()
        if event.date <= timezone.now():
            return Response(
                {'detail': 'Reminder emails can only be sent for upcoming events.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attendees = list(
            Booking.objects.filter(
                event=event,
                status=Booking.STATUS_CONFIRMED,
            ).select_related(
                'user',
                'ticket',
            )
        )
        if not attendees:
            return Response(
                {'detail': 'There are no confirmed attendees to remind for this event.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = send_event_reminder_emails(event, attendees, fail_silently=False)
        except Exception:
            return Response(
                {'detail': 'Reminder emails could not be sent right now. Please try again.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        sent_count = result['sent_count']
        failed_count = result['failed_count']

        if sent_count == 0:
            return Response(
                {'detail': 'Reminder emails could not be sent right now. Please try again.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        message = f'Reminder emails sent to {sent_count} attendee{"s" if sent_count != 1 else ""}.'
        if failed_count:
            message += f' {failed_count} reminder{"s" if failed_count != 1 else ""} could not be sent.'

        return Response(
            {
                'message': message,
                'sent_count': sent_count,
                'failed_count': failed_count,
                'event': {
                    'id': str(event.id),
                    'title': event.title,
                },
            },
            status=status.HTTP_200_OK,
        )
