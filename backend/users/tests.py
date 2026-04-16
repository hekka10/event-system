from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from events.models import Category, Event
from users.models import StudentVerification


User = get_user_model()


class UserFeatureTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='student@example.com',
            username='student',
            password='password123',
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='password123',
        )
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='password123',
        )
        self.category = Category.objects.create(name='Workshop')
        self.event = Event.objects.create(
            title='Student Workshop',
            description='Workshop',
            date=timezone.now() + timedelta(days=7),
            location='Campus Lab',
            category=self.category,
            price=Decimal('100.00'),
            capacity=50,
            organizer=self.organizer,
            is_approved=True,
        )

    def test_register_returns_tokens_and_creates_email_auth_user(self):
        response = self.client.post(
            reverse('register'),
            {
                'email': 'newuser@example.com',
                'username': 'newuser',
                'password': 'StrongPassword123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        created_user = User.objects.get(email='newuser@example.com')
        self.assertEqual(created_user.auth_provider, User.AUTH_PROVIDER_EMAIL)
        self.assertTrue(created_user.check_password('StrongPassword123'))

    def test_login_accepts_email_and_returns_jwt_payload(self):
        response = self.client.post(
            reverse('login'),
            {
                'email': '  STUDENT@EXAMPLE.COM  ',
                'password': 'password123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['email'], 'student@example.com')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='no-reply@test.com',
        FRONTEND_BASE_URL='http://localhost:5173',
    )
    def test_password_reset_request_sends_email_for_existing_email_user(self):
        mail.outbox = []

        response = self.client.post(
            reverse('password_reset_request'),
            {'email': '  STUDENT@EXAMPLE.COM  '},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn('If an account with that email exists', response.data['message'])
        self.assertIn(
            f"/reset-password/{urlsafe_base64_encode(force_bytes(self.user.pk))}/",
            mail.outbox[0].body,
        )

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='no-reply@test.com',
    )
    def test_password_reset_request_is_generic_for_unknown_email(self):
        mail.outbox = []

        response = self.client.post(
            reverse('password_reset_request'),
            {'email': 'missing@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn('If an account with that email exists', response.data['message'])

    def test_password_reset_confirm_updates_password_with_valid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            reverse('password_reset_confirm'),
            {
                'uid': uid,
                'token': token,
                'password': 'NewStrongPassword123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPassword123'))

    def test_password_reset_confirm_rejects_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(
            reverse('password_reset_confirm'),
            {
                'uid': uid,
                'token': 'invalid-token',
                'password': 'NewStrongPassword123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('invalid or has expired', str(response.data['detail']))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('password123'))

    def test_profile_endpoint_requires_authentication(self):
        unauthenticated_response = self.client.get(reverse('me'))
        self.assertEqual(unauthenticated_response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        authenticated_response = self.client.get(reverse('me'))

        self.assertEqual(authenticated_response.status_code, status.HTTP_200_OK)
        self.assertEqual(authenticated_response.data['email'], self.user.email)

    def test_admin_only_student_verification_list_blocks_regular_users(self):
        self.client.force_authenticate(user=self.user)
        forbidden_response = self.client.get(reverse('student_verification_admin_list'))
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        allowed_response = self.client.get(reverse('student_verification_admin_list'))
        self.assertEqual(allowed_response.status_code, status.HTTP_200_OK)

    @patch('users.views.verify_google_id_token')
    def test_google_login_creates_user_and_returns_tokens(self, mock_verify_google_id_token):
        mock_verify_google_id_token.return_value = {
            'sub': 'google-sub-123',
            'email': 'googleuser@example.com',
            'email_verified': 'true',
            'name': 'Google User',
            'aud': 'test-client-id',
        }

        response = self.client.post(
            reverse('google_login'),
            {'id_token': 'fake-id-token'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertTrue(User.objects.filter(email='googleuser@example.com', google_sub='google-sub-123').exists())

    def test_student_verification_review_enables_discounted_checkout(self):
        self.client.force_authenticate(user=self.user)
        submission_response = self.client.post(
            reverse('student_verification_submission'),
            {
                'student_email': 'student@college.edu',
                'student_id': 'STU-001',
                'institution_name': 'Campus College',
                'notes': 'Please verify my account.',
            },
            format='multipart',
        )

        self.assertEqual(submission_response.status_code, status.HTTP_201_CREATED)
        verification_id = submission_response.data['id']

        self.client.force_authenticate(user=self.admin)
        review_response = self.client.post(
            reverse('student_verification_review', args=[verification_id]),
            {'status': StudentVerification.STATUS_APPROVED},
            format='json',
        )

        self.assertEqual(review_response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.user)
        payment_response = self.client.post(
            reverse('payment_initiate'),
            {'event': str(self.event.id)},
            format='json',
        )

        self.assertEqual(payment_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(payment_response.data['booking']['is_student'])
        self.assertEqual(Decimal(payment_response.data['booking']['discount_amount']), Decimal('20.00'))
        self.assertEqual(Decimal(payment_response.data['booking']['total_price']), Decimal('80.00'))

    def test_pending_student_verification_does_not_apply_discount(self):
        StudentVerification.objects.create(
            user=self.user,
            student_email='student@college.edu',
            student_id='STU-PENDING',
            institution_name='Campus College',
            status=StudentVerification.STATUS_PENDING,
        )

        self.client.force_authenticate(user=self.user)
        payment_response = self.client.post(
            reverse('payments_initiate'),
            {'event': str(self.event.id)},
            format='json',
        )

        self.assertEqual(payment_response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(payment_response.data['booking']['is_student'])
        self.assertEqual(Decimal(payment_response.data['booking']['discount_amount']), Decimal('0.00'))
        self.assertEqual(Decimal(payment_response.data['booking']['total_price']), Decimal('100.00'))

    def test_rejected_student_verification_does_not_apply_discount(self):
        StudentVerification.objects.create(
            user=self.user,
            student_email='student@college.edu',
            student_id='STU-REJECTED',
            institution_name='Campus College',
            status=StudentVerification.STATUS_REJECTED,
            rejection_reason='Document mismatch',
        )

        self.client.force_authenticate(user=self.user)
        payment_response = self.client.post(
            reverse('payments_initiate'),
            {'event': str(self.event.id)},
            format='json',
        )

        self.assertEqual(payment_response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(payment_response.data['booking']['is_student'])
        self.assertEqual(Decimal(payment_response.data['booking']['discount_amount']), Decimal('0.00'))
        self.assertEqual(Decimal(payment_response.data['booking']['total_price']), Decimal('100.00'))

    def test_student_alias_routes_submit_status_and_approve_flow(self):
        proof = SimpleUploadedFile(
            'student-id.png',
            b'fake-image-content',
            content_type='image/png',
        )

        self.client.force_authenticate(user=self.user)
        submission_response = self.client.post(
            reverse('student_submit'),
            {
                'student_email': 'student@college.edu',
                'student_id': 'STU-002',
                'student_id_image': proof,
                'institution_name': 'Campus College',
                'notes': 'Updated card upload.',
            },
            format='multipart',
        )

        self.assertEqual(submission_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('student_id_image', submission_response.data)
        self.assertIsNone(submission_response.data['verified_at'])
        verification_id = submission_response.data['id']

        status_response = self.client.get(reverse('student_status'))
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(status_response.data['student_id'], 'STU-002')

        self.client.force_authenticate(user=self.admin)
        approval_response = self.client.post(
            reverse('student_approve'),
            {
                'verification_id': verification_id,
                'status': StudentVerification.STATUS_APPROVED,
            },
            format='json',
        )

        self.assertEqual(approval_response.status_code, status.HTTP_200_OK)
        self.assertEqual(approval_response.data['status'], StudentVerification.STATUS_APPROVED)
        self.assertIsNotNone(approval_response.data['verified_at'])
