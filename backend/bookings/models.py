from io import BytesIO
from decimal import Decimal
import uuid

import qrcode
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone


class Booking(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_FAILED, 'Failed'),
    ]

    SOURCE_ONLINE = 'ONLINE'
    SOURCE_OFFLINE = 'OFFLINE'
    SOURCE_CHOICES = [
        (SOURCE_ONLINE, 'Online'),
        (SOURCE_OFFLINE, 'Offline'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    booking_source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_ONLINE,
    )
    is_student = models.BooleanField(default=False)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(base_price__gte=0),
                name='booking_base_price_gte_zero',
            ),
            models.CheckConstraint(
                condition=models.Q(discount_amount__gte=0),
                name='booking_discount_amount_gte_zero',
            ),
            models.CheckConstraint(
                condition=models.Q(total_price__gte=0),
                name='booking_total_price_gte_zero',
            ),
            models.CheckConstraint(
                condition=models.Q(discount_amount__lte=models.F('base_price')),
                name='booking_discount_not_above_base_price',
            ),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.event.title}"

    def clean(self):
        errors = {}

        if self.base_price is not None and self.base_price < 0:
            errors['base_price'] = 'Base price cannot be negative.'

        if self.discount_amount is not None and self.discount_amount < 0:
            errors['discount_amount'] = 'Discount amount cannot be negative.'

        if (
            self.base_price is not None
            and self.discount_amount is not None
            and self.discount_amount > self.base_price
        ):
            errors['discount_amount'] = 'Discount amount cannot exceed base price.'

        if self.total_price is not None and self.total_price < 0:
            errors['total_price'] = 'Total price cannot be negative.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def confirm(self):
        """
        Confirm the booking after a successful payment and send the QR ticket email once.
        """
        if self.status == self.STATUS_CONFIRMED and hasattr(self, 'ticket'):
            return self.ticket

        self.status = self.STATUS_CONFIRMED
        self.confirmed_at = self.confirmed_at or timezone.now()
        self.save(update_fields=['status', 'confirmed_at', 'updated_at'])

        ticket, _ = Ticket.objects.get_or_create(booking=self)

        from .services import send_booking_confirmation_email

        send_booking_confirmation_email(self, ticket)
        return ticket

    def mark_failed(self):
        if self.status == self.STATUS_CONFIRMED:
            return

        self.status = self.STATUS_FAILED
        self.save(update_fields=['status', 'updated_at'])


class Payment(models.Model):
    PROVIDER_MOCK = 'MOCK'
    PROVIDER_CASH = 'CASH'
    PROVIDER_FREE = 'FREE'
    PROVIDER_CHOICES = [
        (PROVIDER_MOCK, 'Sandbox Gateway'),
        (PROVIDER_CASH, 'Cash'),
        (PROVIDER_FREE, 'Free Booking'),
    ]

    STATUS_INITIATED = 'INITIATED'
    STATUS_PENDING = 'PENDING'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_INITIATED, 'Initiated'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default=PROVIDER_MOCK)
    method = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INITIATED)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    external_reference = models.CharField(max_length=100, unique=True)
    provider_reference = models.CharField(max_length=255, blank=True)
    checkout_url = models.URLField(blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name='payment_amount_gte_zero',
            ),
        ]

    def __str__(self):
        return f"{self.external_reference} - {self.status}"

    def clean(self):
        if self.amount is not None and self.amount < 0:
            raise ValidationError({'amount': 'Payment amount cannot be negative.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='ticket')
    ticket_code = models.CharField(max_length=100, unique=True, blank=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    is_scanned = models.BooleanField(default=False)
    scanned_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_in_tickets',
    )

    class Meta:
        ordering = ['-booking__created_at']

    @classmethod
    def generate_unique_ticket_code(cls):
        while True:
            candidate = f"TICKET-{uuid.uuid4().hex[:12].upper()}"
            if not cls.objects.filter(ticket_code=candidate).exists():
                return candidate

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            self.ticket_code = self.generate_unique_ticket_code()

        if not self.qr_code:
            self.generate_qr()

        super().save(*args, **kwargs)

    def generate_qr(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.ticket_code)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        filename = f"{self.ticket_code}.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    def mark_checked_in(self, checked_in_by):
        if self.is_scanned:
            return False

        self.is_scanned = True
        self.scanned_at = timezone.now()
        self.checked_in_by = checked_in_by
        self.save(update_fields=['is_scanned', 'scanned_at', 'checked_in_by'])
        return True

    def __str__(self):
        return self.ticket_code
