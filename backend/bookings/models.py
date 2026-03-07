from django.db import models
from django.conf import settings
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_student = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.event.title}"

class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='ticket')
    ticket_code = models.CharField(max_length=100, unique=True, blank=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    is_scanned = models.BooleanField(default=False)
    scanned_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            self.ticket_code = f"TICKET-{uuid.uuid4().hex[:12].upper()}"
        
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
        qr.add_data(f"TICKET_ID:{self.id}|CODE:{self.ticket_code}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f"{self.ticket_code}.png"
        self.qr_code.save(filename, File(buffer), save=False)

    def __str__(self):
        return self.ticket_code
