from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import StudentVerification
from .serializers import (
    GoogleOAuthSerializer,
    RegisterSerializer,
    StudentVerificationApproveRequestSerializer,
    StudentVerificationReviewSerializer,
    StudentVerificationSerializer,
    UserSerializer,
)
from .services import build_auth_response, verify_google_id_token


User = get_user_model()


def _build_unique_username(seed):
    base = ''.join(ch for ch in seed.lower() if ch.isalnum()) or 'user'
    candidate = base[:150]
    suffix = 1

    while User.objects.filter(username=candidate).exists():
        trimmed_base = base[: max(1, 150 - len(str(suffix)) - 1)]
        candidate = f"{trimmed_base}{suffix}"
        suffix += 1

    return candidate


def _serialize_student_verification(verification, request):
    serializer = StudentVerificationSerializer(verification, context={'request': request})
    return serializer.data


def _apply_student_verification_review(verification, validated_data, reviewer):
    verification.status = validated_data['status']
    verification.rejection_reason = validated_data.get('rejection_reason', '').strip()
    verification.approved_by = reviewer
    verification.reviewed_at = timezone.now()
    verification.verified_at = (
        verification.reviewed_at
        if verification.status == StudentVerification.STATUS_APPROVED
        else None
    )
    verification.save(
        update_fields=[
            'status',
            'rejection_reason',
            'approved_by',
            'verified_at',
            'reviewed_at',
            'updated_at',
        ]
    )
    return verification


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(build_auth_response(user), status=status.HTTP_201_CREATED)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_value = attrs.get(self.username_field, '')
        if isinstance(username_value, str):
            attrs[self.username_field] = username_value.strip().lower()
        super().validate(attrs)
        return build_auth_response(self.user)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class GoogleOAuthLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleOAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        google_payload = verify_google_id_token(serializer.validated_data['id_token'])
        email = google_payload['email'].strip().lower()
        google_sub = google_payload['sub']

        user = User.objects.filter(google_sub=google_sub).first()
        if not user:
            user = User.objects.filter(email=email).first()

        if user is None:
            username_seed = google_payload.get('name') or email.split('@')[0]
            user = User(
                email=email,
                username=_build_unique_username(username_seed),
                auth_provider=User.AUTH_PROVIDER_GOOGLE,
                google_sub=google_sub,
            )
            user.set_unusable_password()
        else:
            user.auth_provider = User.AUTH_PROVIDER_GOOGLE
            user.google_sub = google_sub

        user.save()
        return Response(build_auth_response(user), status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class StudentVerificationSubmissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        verification = StudentVerification.objects.filter(user=request.user).first()
        if verification is None:
            return Response(None, status=status.HTTP_200_OK)

        return Response(_serialize_student_verification(verification, request))

    def post(self, request):
        serializer = StudentVerificationSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        verification = serializer.save()
        return Response(
            _serialize_student_verification(verification, request),
            status=status.HTTP_201_CREATED,
        )


class StudentVerificationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        verification = StudentVerification.objects.filter(user=request.user).first()
        if verification is None:
            return Response(None, status=status.HTTP_200_OK)

        return Response(_serialize_student_verification(verification, request))


class StudentVerificationSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StudentVerificationSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        verification = serializer.save()
        return Response(
            _serialize_student_verification(verification, request),
            status=status.HTTP_201_CREATED,
        )


class StudentVerificationAdminListView(generics.ListAPIView):
    serializer_class = StudentVerificationSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = StudentVerification.objects.select_related('user', 'approved_by')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        return queryset.order_by('-created_at')


class StudentVerificationReviewView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        verification = generics.get_object_or_404(StudentVerification, pk=pk)
        serializer = StudentVerificationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification = _apply_student_verification_review(
            verification,
            serializer.validated_data,
            request.user,
        )

        return Response(_serialize_student_verification(verification, request), status=status.HTTP_200_OK)


class StudentVerificationApproveView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = StudentVerificationApproveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification = generics.get_object_or_404(
            StudentVerification,
            pk=serializer.validated_data['verification_id'],
        )
        verification = _apply_student_verification_review(
            verification,
            serializer.validated_data,
            request.user,
        )

        return Response(_serialize_student_verification(verification, request), status=status.HTTP_200_OK)
