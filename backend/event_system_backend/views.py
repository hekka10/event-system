from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking, Payment, Ticket
from events.models import Event
from users.models import StudentVerification


User = get_user_model()


class AdminDashboardStats(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_users = User.objects.count()
        total_events = Event.objects.count()
        total_bookings = Booking.objects.count()
        confirmed_bookings = Booking.objects.filter(status=Booking.STATUS_CONFIRMED).count()
        pending_bookings = Booking.objects.filter(status=Booking.STATUS_PENDING).count()
        total_revenue = (
            Booking.objects.filter(status=Booking.STATUS_CONFIRMED).aggregate(Sum('total_price'))['total_price__sum']
            or 0.00
        )
        total_checked_in = Ticket.objects.filter(is_scanned=True).count()

        latest_bookings = Booking.objects.select_related('user', 'event').order_by('-created_at')[:5]
        bookings_data = [
            {
                "id": str(booking.id),
                "user": booking.user.email,
                "event": booking.event.title,
                "amount": booking.total_price,
                "date": booking.created_at,
                "status": booking.status,
            }
            for booking in latest_bookings
        ]

        recent_payments = Payment.objects.select_related('user').order_by('-created_at')[:5]
        payments_data = [
            {
                "id": str(payment.id),
                "reference": payment.external_reference,
                "user": payment.user.email,
                "amount": payment.amount,
                "status": payment.status,
                "provider": payment.provider,
            }
            for payment in recent_payments
        ]

        pending_events = Event.objects.select_related('organizer').filter(is_approved=False).order_by('-created_at')
        pending_events_data = [
            {
                "id": str(event.id),
                "title": event.title,
                "organizer": event.organizer.email,
                "created_at": event.created_at,
            }
            for event in pending_events
        ]

        pending_student_verifications = StudentVerification.objects.select_related('user').filter(
            status=StudentVerification.STATUS_PENDING
        ).order_by('-created_at')
        student_verification_data = [
            {
                "id": str(verification.id),
                "user": verification.user.email,
                "student_email": verification.student_email,
                "institution_name": verification.institution_name,
                "created_at": verification.created_at,
            }
            for verification in pending_student_verifications[:5]
        ]

        recent_check_ins = Ticket.objects.select_related(
            'booking',
            'booking__event',
            'booking__user',
            'checked_in_by',
        ).filter(is_scanned=True).order_by('-scanned_at')[:5]
        check_in_data = [
            {
                "ticket_code": ticket.ticket_code,
                "event": ticket.booking.event.title,
                "attendee": ticket.booking.user.email,
                "checked_in_by": ticket.checked_in_by.email if ticket.checked_in_by else None,
                "scanned_at": ticket.scanned_at,
            }
            for ticket in recent_check_ins
        ]

        return Response(
            {
                "total_users": total_users,
                "total_events": total_events,
                "total_bookings": total_bookings,
                "confirmed_bookings": confirmed_bookings,
                "pending_bookings": pending_bookings,
                "total_revenue": total_revenue,
                "total_checked_in": total_checked_in,
                "pending_student_verification_count": pending_student_verifications.count(),
                "latest_bookings": bookings_data,
                "recent_payments": payments_data,
                "recent_check_ins": check_in_data,
                "pending_events": pending_events_data,
                "pending_student_verifications": student_verification_data,
            }
        )
