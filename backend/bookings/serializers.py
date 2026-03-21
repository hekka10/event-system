from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from events.models import Event
from events.serializers import EventSerializer

from .models import Booking, Payment, Ticket
from .services import calculate_booking_pricing


User = get_user_model()


class TicketSerializer(serializers.ModelSerializer):
    checked_in_by_email = serializers.ReadOnlyField(source='checked_in_by.email')

    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_code',
            'qr_code',
            'is_scanned',
            'scanned_at',
            'checked_in_by',
            'checked_in_by_email',
        ]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'provider',
            'method',
            'status',
            'amount',
            'currency',
            'external_reference',
            'provider_reference',
            'checkout_url',
            'paid_at',
            'verified_at',
            'created_at',
            'updated_at',
        ]


class BookingSerializer(serializers.ModelSerializer):
    event_details = EventSerializer(source='event', read_only=True)
    ticket = TicketSerializer(read_only=True)
    user_email = serializers.ReadOnlyField(source='user.email')
    latest_payment = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'user_email',
            'event',
            'event_details',
            'status',
            'booking_source',
            'is_student',
            'base_price',
            'discount_amount',
            'total_price',
            'ticket',
            'latest_payment',
            'confirmed_at',
            'created_at',
        ]
        read_only_fields = [
            'user',
            'status',
            'booking_source',
            'is_student',
            'base_price',
            'discount_amount',
            'total_price',
            'ticket',
            'latest_payment',
            'confirmed_at',
            'created_at',
        ]

    def get_latest_payment(self, obj):
        payment = obj.payments.order_by('-created_at').first()
        if not payment:
            return None
        return PaymentSerializer(payment).data


class BookingRequestValidationMixin:
    def validate_booking_request(self, user, event):
        if event.date <= timezone.now():
            raise serializers.ValidationError({'event': 'Cannot book an event that is in the past.'})

        if not event.is_approved:
            raise serializers.ValidationError({'event': 'Cannot book an unapproved event.'})

        existing_booking = Booking.objects.filter(user=user, event=event).exclude(
            status__in=[Booking.STATUS_CANCELLED, Booking.STATUS_FAILED]
        )
        if self.instance is not None:
            existing_booking = existing_booking.exclude(pk=self.instance.pk)

        if existing_booking.exists():
            raise serializers.ValidationError({'non_field_errors': 'You have already booked this event.'})

        confirmed_bookings = Booking.objects.filter(
            event=event,
            status=Booking.STATUS_CONFIRMED,
        ).count()
        if confirmed_bookings >= event.capacity:
            raise serializers.ValidationError({'event': 'This event is already at full capacity.'})


class BookingCreateSerializer(BookingRequestValidationMixin, serializers.ModelSerializer):
    user_email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = Booking
        fields = ['event', 'user_email']

    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        email = attrs.get('user_email')

        if email and request.user.is_staff:
            user = User.objects.filter(email=email.strip().lower()).first() or user

        attrs['target_user'] = user
        self.validate_booking_request(user, attrs['event'])
        return attrs

    def create(self, validated_data):
        user = validated_data.pop('target_user')
        validated_data.pop('user_email', None)
        pricing = calculate_booking_pricing(user, validated_data['event'])

        return Booking.objects.create(
            user=user,
            event=validated_data['event'],
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=pricing['is_student'],
            base_price=pricing['base_price'],
            discount_amount=pricing['discount_amount'],
            total_price=pricing['total_price'],
        )


class PaymentInitiationSerializer(BookingRequestValidationMixin, serializers.Serializer):
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    def validate(self, attrs):
        self.validate_booking_request(self.context['request'].user, attrs['event'])
        return attrs


class PaymentVerificationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[Payment.STATUS_SUCCESS, Payment.STATUS_FAILED])
    provider_reference = serializers.CharField(required=False, allow_blank=True)
    provider_response = serializers.JSONField(required=False)


class PaymentWebhookSerializer(serializers.Serializer):
    payment_reference = serializers.CharField()
    status = serializers.ChoiceField(choices=[Payment.STATUS_SUCCESS, Payment.STATUS_FAILED])
    provider_reference = serializers.CharField(required=False, allow_blank=True)
    provider_response = serializers.JSONField(required=False)


class OfflineBookingSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    username = serializers.CharField(required=False, allow_blank=True)
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    def validate(self, attrs):
        event = attrs['event']
        if event.date <= timezone.now():
            raise serializers.ValidationError({'event': 'Cannot create a walk-in booking for a past event.'})

        if not event.is_approved:
            raise serializers.ValidationError({'event': 'Only approved events can accept walk-in bookings.'})

        return attrs


class TicketScanSerializer(serializers.Serializer):
    ticket_code = serializers.CharField()
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all(), required=False)
    mark_checked_in = serializers.BooleanField(default=True)

    def validate_ticket_code(self, value):
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError('Ticket code is required.')
        return value
