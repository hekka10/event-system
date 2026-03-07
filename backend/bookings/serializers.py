from rest_framework import serializers
from .models import Booking, Ticket
from events.serializers import EventSerializer
from django.core.mail import send_mail
from django.conf import settings

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_code', 'qr_code', 'is_scanned', 'scanned_at']

class BookingSerializer(serializers.ModelSerializer):
    event_details = EventSerializer(source='event', read_only=True)
    ticket = TicketSerializer(read_only=True)
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'user_email', 'event', 'event_details', 
            'status', 'is_student', 'total_price', 'ticket', 'created_at'
        ]
        read_only_fields = ['user', 'status', 'total_price', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        event = validated_data['event']
        
        # Check student status (simple email domain check)
        is_student = user.email.endswith('@student.edu') or validated_data.get('is_student', False)
        
        # Apply discount if student
        price = event.price
        if is_student:
            price = price * 0.80 # 20% discount
            
        validated_data['user'] = user
        validated_data['is_student'] = is_student
        validated_data['total_price'] = price
        validated_data['status'] = 'CONFIRMED' # Auto-confirm for now (MVP)
        
        booking = super().create(validated_data)
        
        # Create ticket automatically
        Ticket.objects.create(booking=booking)
        
        # Send confirmation email
        try:
            subject = f"Booking Confirmation: {event.title}"
            message = f"Hello {user.username or user.email},\n\nYour booking for {event.title} has been confirmed!\n\nTicket Code: {booking.ticket.ticket_code}\nDate: {event.date}\nLocation: {event.location}\n\nThank you for using SmartEvents!"
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            
        return booking
