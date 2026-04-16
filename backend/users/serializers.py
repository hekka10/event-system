from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from .models import StudentVerification


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    student_verification_status = serializers.SerializerMethodField()
    is_student_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'is_staff',
            'is_superuser',
            'auth_provider',
            'student_verification_status',
            'is_student_verified',
        )

    def get_student_verification_status(self, obj):
        verification = getattr(obj, 'student_verification', None)
        return getattr(verification, 'status', None)

    def get_is_student_verified(self, obj):
        verification = getattr(obj, 'student_verification', None)
        return bool(getattr(verification, 'is_approved', False))


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return email

    def validate_username(self, value):
        username = value.strip()
        if not username:
            raise serializers.ValidationError('Username is required.')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return username

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            auth_provider=User.AUTH_PROVIDER_EMAIL,
        )
        return user


class GoogleOAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                {'detail': 'This password reset link is invalid or has expired.'}
            )

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError(
                {'detail': 'This password reset link is invalid or has expired.'}
            )

        validate_password(attrs['password'], user=user)
        attrs['user'] = user
        return attrs


class StudentVerificationSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    reviewed_by_email = serializers.ReadOnlyField(source='approved_by.email')
    student_id_image = serializers.FileField(
        source='supporting_document',
        required=False,
        allow_null=True,
    )

    class Meta:
        model = StudentVerification
        fields = [
            'id',
            'user',
            'user_email',
            'student_email',
            'student_id',
            'student_id_image',
            'institution_name',
            'supporting_document',
            'notes',
            'status',
            'rejection_reason',
            'approved_by',
            'reviewed_by_email',
            'verified_at',
            'reviewed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'user',
            'status',
            'rejection_reason',
            'approved_by',
            'verified_at',
            'reviewed_at',
            'created_at',
            'updated_at',
        ]

    def validate_student_email(self, value):
        return value.strip().lower()

    def validate_student_id(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Student ID is required.')
        return value

    def validate_institution_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Institution name is required.')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        verification, _ = StudentVerification.objects.update_or_create(
            user=user,
            defaults={
                **validated_data,
                'status': StudentVerification.STATUS_PENDING,
                'rejection_reason': '',
                'approved_by': None,
                'verified_at': None,
                'reviewed_at': None,
            },
        )
        return verification


class StudentVerificationReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            StudentVerification.STATUS_APPROVED,
            StudentVerification.STATUS_REJECTED,
        ]
    )
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if (
            attrs['status'] == StudentVerification.STATUS_REJECTED
            and not attrs.get('rejection_reason', '').strip()
        ):
            raise serializers.ValidationError(
                {'rejection_reason': 'A rejection reason is required when rejecting.'}
            )
        return attrs


class StudentVerificationApproveRequestSerializer(StudentVerificationReviewSerializer):
    verification_id = serializers.UUIDField()
