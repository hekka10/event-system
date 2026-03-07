from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from events.models import Event
from bookings.models import Booking
from django.db.models import Sum

User = get_user_model()

class AdminDashboardStats(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_users = User.objects.count()
        total_events = Event.objects.count()
        total_bookings = Booking.objects.count()
        total_revenue = Booking.objects.filter(status='CONFIRMED').aggregate(Sum('total_price'))['total_price__sum'] or 0.00

        # Latest bookings
        latest_bookings = Booking.objects.order_by('-created_at')[:5]
        bookings_data = [
            {
                "id": str(b.id),
                "user": b.user.email,
                "event": b.event.title,
                "amount": b.total_price,
                "date": b.created_at
            } for b in latest_bookings
        ]

        return Response({
            "total_users": total_users,
            "total_events": total_events,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "latest_bookings": bookings_data
        })
