from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    AUTH_PROVIDER_EMAIL = 'EMAIL'
    AUTH_PROVIDER_GOOGLE = 'GOOGLE'
    AUTH_PROVIDER_CHOICES = [
        (AUTH_PROVIDER_EMAIL, 'Email'),
        (AUTH_PROVIDER_GOOGLE, 'Google'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    auth_provider = models.CharField(
        max_length=20,
        choices=AUTH_PROVIDER_CHOICES,
        default=AUTH_PROVIDER_EMAIL,
    )
    google_sub = models.CharField(max_length=255, unique=True, null=True, blank=True)

    # Use email instead of username for login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class StudentVerification(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='student_verification',
    )
    student_email = models.EmailField()
    student_id = models.CharField(max_length=100)
    institution_name = models.CharField(max_length=255)
    supporting_document = models.FileField(
        upload_to='student-verifications/',
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    rejection_reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_student_verifications',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.status}"

    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED
