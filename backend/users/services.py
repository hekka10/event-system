import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken


GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


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


def verify_google_id_token(id_token):
    query = urlencode({"id_token": id_token})
    request = Request(
        f"{GOOGLE_TOKENINFO_URL}?{query}",
        headers={"Accept": "application/json"},
    )

    try:
        with urlopen(request, timeout=10) as response:
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
