from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from events.models import Event
from events.serializers import EventSerializer

from .models import Booking, Payment, Ticket
from .services import create_pending_booking, get_booking_validation_error


User = get_user_model()


class TicketSerializer(serializers.ModelSerializer):
    checked_in_by_email = serializers.ReadOnlyField(source='checked_in_by.email')
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_code',
            'qr_code',
            'qr_code_url',
            'is_scanned',
            'scanned_at',
            'checked_in_by',
            'checked_in_by_email',
        ]

    def get_qr_code_url(self, obj):
        if not obj.qr_code:
            return None

        request = self.context.get('request')
        url = obj.qr_code.url
        if request is None:
            return url
        return request.build_absolute_uri(url)


class PaymentSerializer(serializers.ModelSerializer):
    transaction_ref = serializers.CharField(source='external_reference', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'provider',
            'method',
            'status',
            'amount',
            'currency',
            'transaction_ref',
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
        booking_id = getattr(self.instance, 'pk', None)
        error = get_booking_validation_error(user, event, booking_id_to_ignore=booking_id)
        if error:
            raise serializers.ValidationError(error)


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
        return create_pending_booking(user, validated_data['event'], booking_source=Booking.SOURCE_ONLINE)


class PaymentInitiationSerializer(BookingRequestValidationMixin, serializers.Serializer):
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    def validate(self, attrs):
        self.validate_booking_request(self.context['request'].user, attrs['event'])
        return attrs


class PaymentVerificationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[Payment.STATUS_SUCCESS, Payment.STATUS_FAILED])
    provider_reference = serializers.CharField(required=False, allow_blank=True)
    provider_response = serializers.JSONField(required=False)


class PaymentVerificationRequestSerializer(PaymentVerificationSerializer):
    payment_id = serializers.UUIDField(required=False)
    transaction_ref = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        if not attrs.get('payment_id') and not attrs.get('transaction_ref'):
            raise serializers.ValidationError(
                'Either payment_id or transaction_ref is required.'
            )
        return attrs


class PaymentWebhookSerializer(serializers.Serializer):
    payment_reference = serializers.CharField()
    status = serializers.ChoiceField(choices=[Payment.STATUS_SUCCESS, Payment.STATUS_FAILED])
    provider_reference = serializers.CharField(required=False, allow_blank=True)
    provider_response = serializers.JSONField(required=False)


class OfflineBookingSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    username = serializers.CharField(required=False, allow_blank=True)
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    def validate_user_email(self, value):
        return value.strip().lower()

    def validate_username(self, value):
        return value.strip()

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
