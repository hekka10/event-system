from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import uuid

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    parking_info = models.TextField(blank=True)
    parking_map_url = models.URLField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='events')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    capacity = models.PositiveIntegerField()
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Track the organizer (user who created the event)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_events',
    )

    class Meta:
        ordering = ['date', '-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name='event_price_gte_zero',
            ),
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1),
                name='event_capacity_gte_one',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(latitude__isnull=True, longitude__isnull=True)
                    | models.Q(latitude__isnull=False, longitude__isnull=False)
                ),
                name='event_coordinates_complete',
            ),
            models.CheckConstraint(
                condition=models.Q(latitude__isnull=True) | models.Q(latitude__gte=-90, latitude__lte=90),
                name='event_latitude_valid',
            ),
            models.CheckConstraint(
                condition=models.Q(longitude__isnull=True) | models.Q(longitude__gte=-180, longitude__lte=180),
                name='event_longitude_valid',
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}

        if self.date and self.date <= timezone.now():
            errors['date'] = 'Event date must be in the future.'

        if self.capacity is not None and self.capacity <= 0:
            errors['capacity'] = 'Capacity must be greater than 0.'

        if self.price is not None and self.price < 0:
            errors['price'] = 'Price cannot be negative.'

        has_latitude = self.latitude is not None
        has_longitude = self.longitude is not None

        if has_latitude != has_longitude:
            errors['latitude'] = 'Latitude and longitude must be provided together.'
            errors['longitude'] = 'Latitude and longitude must be provided together.'

        if has_latitude and not (-90 <= self.latitude <= 90):
            errors['latitude'] = 'Latitude must be between -90 and 90.'

        if has_longitude and not (-180 <= self.longitude <= 180):
            errors['longitude'] = 'Longitude must be between -180 and 180.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
