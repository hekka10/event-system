import logging
import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken


GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
logger = logging.getLogger(__name__)


def build_auth_response(user):
    refresh = RefreshToken.for_user(user)
    verification = getattr(user, "student_verification", None)

    return {
        "_id": user.id,
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "token": str(refresh.access_token),
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "auth_provider": user.auth_provider,
        "student_verification_status": getattr(verification, "status", None),
        "is_student_verified": getattr(verification, "is_approved", False),
    }


def build_password_reset_url(user):
    frontend_base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:5173').rstrip('/')
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{frontend_base_url}/reset-password/{uid}/{token}"


def send_password_reset_email(user, fail_silently=False):
    reset_url = build_password_reset_url(user)
    subject = "Reset your SmartEvents password"
    text_body = (
        f"Hello {user.username or user.email},\n\n"
        "We received a request to reset your SmartEvents password.\n"
        f"Reset it here: {reset_url}\n\n"
        "If you did not request this, you can safely ignore this email.\n"
    )
    html_body = f"""
        <p>Hello {user.username or user.email},</p>
        <p>We received a request to reset your SmartEvents password.</p>
        <p><a href="{reset_url}">Reset your password</a></p>
        <p>If you did not request this, you can safely ignore this email.</p>
    """

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_body, "text/html")

    try:
        email.send(fail_silently=fail_silently)
    except Exception:
        logger.exception("Failed to send password reset email for user %s", user.pk)
        raise


def verify_google_id_token(id_token):
    query = urlencode({"id_token": id_token})
    request = Request(
        f"{GOOGLE_TOKENINFO_URL}?{query}",
        headers={"Accept": "application/json"},
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    try:
        with urlopen(request, timeout=10, context=ssl_context) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise ValidationError(
            {"id_token": "Google rejected the supplied token."}
        ) from exc
    except URLError as exc:
        raise ValidationError(
            {"id_token": "Google verification is temporarily unavailable."}
        ) from exc

    if payload.get("error_description"):
        raise ValidationError({"id_token": payload["error_description"]})

    expected_audience = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
    if expected_audience and payload.get("aud") != expected_audience:
        raise ValidationError({"id_token": "Token audience does not match this app."})

    if payload.get("email_verified") not in ["true", True]:
        raise ValidationError({"id_token": "Google account email is not verified."})

    required_fields = ["sub", "email"]
    missing_fields = [field for field in required_fields if not payload.get(field)]
    if missing_fields:
        raise ValidationError(
            {"id_token": f"Google response is missing: {', '.join(missing_fields)}."}
        )

    return payload
