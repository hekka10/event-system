from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Booking
from .serializers import BookingSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users should only see their own bookings unless they are staff
        if self.request.user.is_staff:
            return Booking.objects.all().order_by('-created_at')
        return Booking.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        email = self.request.data.get('user_email')
        
        # If admin provides an email, book for that user
        if email and self.request.user.is_staff:
            target_user = User.objects.filter(email=email).first()
            if target_user:
                user = target_user
        
        serializer.save(user=user)

    def create(self, request, *args, **kwargs):
        # Override create to handle extra logic if needed (already in serializer)
        return super().create(request, *args, **kwargs)
