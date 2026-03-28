from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import Event, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    organizer_email = serializers.ReadOnlyField(source='organizer.email')
    confirmed_booking_count = serializers.SerializerMethodField()
    remaining_capacity = serializers.SerializerMethodField()
    is_sold_out = serializers.SerializerMethodField()
    student_discount_percent = serializers.SerializerMethodField()
    viewer_has_student_discount = serializers.SerializerMethodField()
    viewer_discount_amount = serializers.SerializerMethodField()
    viewer_total_price = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'date', 'location',
            'parking_info', 'parking_map_url', 'latitude', 'longitude',
            'category', 'category_name', 'price', 'capacity',
            'image', 'organizer', 'organizer_email', 'is_approved',
            'confirmed_booking_count', 'remaining_capacity', 'is_sold_out',
            'student_discount_percent', 'viewer_has_student_discount',
            'viewer_discount_amount', 'viewer_total_price',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['organizer', 'is_approved', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Automatically set the organizer to the current user
        validated_data['organizer'] = self.context['request'].user
        return super().create(validated_data)

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()

    def validate_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Event date must be in the future.")
        return value

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be greater than 0.")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_location(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Location is required.")
        return value.strip()

    def validate(self, attrs):
        latitude = attrs.get('latitude', getattr(self.instance, 'latitude', None))
        longitude = attrs.get('longitude', getattr(self.instance, 'longitude', None))

        if (latitude is None) ^ (longitude is None):
            raise serializers.ValidationError(
                "Latitude and longitude must be provided together."
            )

        if latitude is not None and not (-90 <= latitude <= 90):
            raise serializers.ValidationError({'latitude': 'Latitude must be between -90 and 90.'})

        if longitude is not None and not (-180 <= longitude <= 180):
            raise serializers.ValidationError({'longitude': 'Longitude must be between -180 and 180.'})

        return attrs

    def get_confirmed_booking_count(self, obj):
        return getattr(obj, 'confirmed_booking_count_value', obj.bookings.filter(status='CONFIRMED').count())

    def get_remaining_capacity(self, obj):
        return max(obj.capacity - self.get_confirmed_booking_count(obj), 0)

    def get_is_sold_out(self, obj):
        return self.get_remaining_capacity(obj) <= 0

    def _get_viewer_pricing(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return {
                'is_student': False,
                'discount_amount': Decimal('0.00'),
                'total_price': obj.price,
            }

        from bookings.services import calculate_booking_pricing

        return calculate_booking_pricing(user, obj)

    def get_student_discount_percent(self, obj):
        from bookings.services import get_student_discount_rate

        return int(get_student_discount_rate() * 100)

    def get_viewer_has_student_discount(self, obj):
        pricing = self._get_viewer_pricing(obj)
        return pricing['is_student']

    def get_viewer_discount_amount(self, obj):
        pricing = self._get_viewer_pricing(obj)
        return pricing['discount_amount']

    def get_viewer_total_price(self, obj):
        pricing = self._get_viewer_pricing(obj)
        return pricing['total_price']
