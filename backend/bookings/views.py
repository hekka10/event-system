import uuid

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from rest_framework.decorators import action
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking, Payment, Ticket
from .permissions import IsAdminOrEventOrganizer
from .serializers import (
    BookingCreateSerializer,
    BookingSerializer,
    OfflineBookingSerializer,
    PaymentInitiationSerializer,
    PaymentSerializer,
    PaymentVerificationRequestSerializer,
    PaymentVerificationSerializer,
    PaymentWebhookSerializer,
    TicketScanSerializer,
)
from .services import (
    build_frontend_payment_return_url,
    build_payment_reference,
    create_pending_booking,
    create_payment_for_booking,
    create_replacement_payment,
    decode_esewa_callback_data,
    get_booking_validation_error,
    get_esewa_provider_reference,
    get_online_payment_provider,
    get_or_create_offline_user,
    is_esewa_verification_complete,
    process_failed_payment,
    process_successful_payment,
    send_booking_confirmation_email,
    verify_esewa_payment,
)


def get_payment_with_relations():
    return Payment.objects.select_related('booking', 'booking__event', 'user')


def verify_payment_submission(request, payment, validated_data):
    if validated_data['status'] == Payment.STATUS_SUCCESS:
        payment, ticket, capacity_error = process_successful_payment(
            payment,
            provider_reference=validated_data.get('provider_reference', ''),
            provider_response=validated_data.get('provider_response'),
        )
        if capacity_error:
            return Response(
                {
                    'detail': capacity_error,
                    'booking': BookingSerializer(payment.booking, context={'request': request}).data,
                    'payment': PaymentSerializer(payment).data,
                },
                status=status.HTTP_409_CONFLICT,
            )
    else:
        payment = process_failed_payment(
            payment,
            provider_reference=validated_data.get('provider_reference', ''),
            provider_response=validated_data.get('provider_response'),
        )
        ticket = None

    return Response(
        {
            'message': 'Payment verification completed.',
            'next_action': 'BOOKING_CONFIRMED' if payment.status == Payment.STATUS_SUCCESS else 'PAYMENT_FAILED',
            'booking': BookingSerializer(payment.booking, context={'request': request}).data,
            'payment': PaymentSerializer(payment).data,
            'ticket_code': ticket.ticket_code if ticket else None,
        }
    )


def get_esewa_payment_for_callback(request, payment_id=None):
    raw_data = request.query_params.get('data') or request.data.get('data')
    candidate_payment_id = (
        payment_id
        or request.query_params.get('payment_id')
        or request.data.get('payment_id')
    )

    # eSewa can append `?data=...` even when the callback URL already had a query string.
    # Recover that malformed legacy format so in-flight payments still complete.
    if candidate_payment_id and '?data=' in str(candidate_payment_id) and not raw_data:
        candidate_payment_id, raw_data = str(candidate_payment_id).split('?data=', 1)

    callback_payload = decode_esewa_callback_data(raw_data)
    candidate_payment_id = candidate_payment_id or callback_payload.get('transaction_uuid')
    if not candidate_payment_id:
        return None, callback_payload

    try:
        normalized_payment_id = str(uuid.UUID(str(candidate_payment_id)))
    except (ValueError, TypeError, AttributeError):
        fallback_payment_id = callback_payload.get('transaction_uuid')
        if not fallback_payment_id:
            return None, callback_payload
        try:
            normalized_payment_id = str(uuid.UUID(str(fallback_payment_id)))
        except (ValueError, TypeError, AttributeError):
            return None, callback_payload

    payment = get_payment_with_relations().filter(
        pk=normalized_payment_id,
        provider=Payment.PROVIDER_ESEWA,
    ).first()
    return payment, callback_payload


def redirect_to_frontend_payment_result(payment=None, payment_status='failed'):
    return redirect(
        build_frontend_payment_return_url(
            payment=payment,
            payment_status=payment_status,
            gateway='esewa',
        )
    )


class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        queryset = Booking.objects.select_related(
            'user',
            'event',
            'event__category',
            'ticket',
        ).prefetch_related('payments')
        if self.request.user.is_staff:
            return queryset.order_by('-created_at')
        return queryset.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        output_serializer = BookingSerializer(booking, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='send-ticket-email')
    def send_ticket_email(self, request, pk=None):
        booking = self.get_object()

        if booking.status != Booking.STATUS_CONFIRMED:
            return Response(
                {'detail': 'Only confirmed bookings can send ticket emails.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not hasattr(booking, 'ticket'):
            return Response(
                {'detail': 'This booking does not have a ticket yet.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            send_booking_confirmation_email(
                booking,
                ticket=booking.ticket,
                fail_silently=False,
            )
        except Exception:
            return Response(
                {'detail': 'Ticket email could not be sent right now. Please try again.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                'message': f'Ticket email sent to {booking.user.email}.',
                'email': booking.user.email,
                'ticket_code': booking.ticket.ticket_code,
            },
            status=status.HTTP_200_OK,
        )


class PaymentInitiationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentInitiationSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.validated_data['event']
        booking = create_pending_booking(request.user, event, booking_source=Booking.SOURCE_ONLINE)

        if booking.total_price == 0:
            payment = create_payment_for_booking(
                booking,
                provider=Payment.PROVIDER_FREE,
                method='FREE',
                status=Payment.STATUS_SUCCESS,
            )
            payment, ticket, capacity_error = process_successful_payment(
                payment,
                provider_reference=build_payment_reference('FREE'),
                provider_response={'source': 'free-booking'},
            )
            if capacity_error:
                return Response(
                    {
                        'detail': capacity_error,
                        'booking': BookingSerializer(booking, context={'request': request}).data,
                        'payment': PaymentSerializer(payment).data,
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            return Response(
                {
                    'message': 'Free booking confirmed successfully.',
                    'next_action': 'CONFIRMED',
                    'booking': BookingSerializer(booking, context={'request': request}).data,
                    'payment': PaymentSerializer(payment).data,
                    'ticket_code': ticket.ticket_code,
                },
                status=status.HTTP_201_CREATED,
            )

        provider = get_online_payment_provider()
        try:
            payment = create_payment_for_booking(booking, provider=provider, method='ONLINE')
        except ValueError as exc:
            booking.mark_failed()
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        next_action = 'REDIRECT_TO_ESEWA' if provider == Payment.PROVIDER_ESEWA else 'COMPLETE_PAYMENT'
        message = (
            'eSewa payment initiated successfully.'
            if provider == Payment.PROVIDER_ESEWA
            else 'Payment initiated successfully.'
        )
        return Response(
            {
                'message': message,
                'next_action': next_action,
                'booking': BookingSerializer(booking, context={'request': request}).data,
                'payment': PaymentSerializer(payment).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, payment_id):
        payment = get_object_or_404(
            get_payment_with_relations(),
            pk=payment_id,
        )

        if not (request.user.is_staff or payment.user_id == request.user.id):
            return Response({'detail': 'You do not have permission to view this payment.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(
            {
                'payment': PaymentSerializer(payment).data,
                'booking': BookingSerializer(payment.booking, context={'request': request}).data,
            }
        )


class PaymentRetryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        payment = get_object_or_404(
            get_payment_with_relations(),
            pk=payment_id,
        )

        if not (request.user.is_staff or payment.user_id == request.user.id):
            return Response(
                {'detail': 'You do not have permission to retry this payment.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            new_payment = create_replacement_payment(payment)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        next_action = (
            'REDIRECT_TO_ESEWA'
            if new_payment.provider == Payment.PROVIDER_ESEWA
            else 'COMPLETE_PAYMENT'
        )
        return Response(
            {
                'message': 'A fresh payment session was created.',
                'next_action': next_action,
                'booking': BookingSerializer(new_payment.booking, context={'request': request}).data,
                'payment': PaymentSerializer(new_payment).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        payment = get_object_or_404(
            get_payment_with_relations(),
            pk=payment_id,
        )

        if not (request.user.is_staff or payment.user_id == request.user.id):
            return Response({'detail': 'You do not have permission to verify this payment.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PaymentVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return verify_payment_submission(request, payment, serializer.validated_data)

class PaymentVerificationRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment_filters = {}
        payment_id = serializer.validated_data.get('payment_id')
        transaction_ref = serializer.validated_data.get('transaction_ref')

        if payment_id:
            payment_filters['pk'] = payment_id
        else:
            payment_filters['external_reference'] = transaction_ref

        payment = get_object_or_404(get_payment_with_relations(), **payment_filters)

        if not (request.user.is_staff or payment.user_id == request.user.id):
            return Response(
                {'detail': 'You do not have permission to verify this payment.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return verify_payment_submission(request, payment, serializer.validated_data)


class PaymentWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        expected_secret = getattr(settings, 'PAYMENT_WEBHOOK_SECRET', '')
        received_secret = request.headers.get('X-Payment-Webhook-Secret', '')

        if expected_secret and received_secret != expected_secret:
            return Response({'detail': 'Invalid webhook secret.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PaymentWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = get_object_or_404(
            Payment.objects.select_related('booking'),
            external_reference=serializer.validated_data['payment_reference'],
        )

        if serializer.validated_data['status'] == Payment.STATUS_SUCCESS:
            payment, _, capacity_error = process_successful_payment(
                payment,
                provider_reference=serializer.validated_data.get('provider_reference', ''),
                provider_response=serializer.validated_data.get('provider_response'),
            )
            if capacity_error:
                return Response(
                    {
                        'status': payment.status,
                        'detail': capacity_error,
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            payment = process_failed_payment(
                payment,
                provider_reference=serializer.validated_data.get('provider_reference', ''),
                provider_response=serializer.validated_data.get('provider_response'),
            )

        return Response({'status': payment.status}, status=status.HTTP_200_OK)


class EsewaSuccessView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, payment_id=None):
        return self._handle(request, payment_id=payment_id)

    def post(self, request, payment_id=None):
        return self._handle(request, payment_id=payment_id)

    def _handle(self, request, payment_id=None):
        payment, callback_payload = get_esewa_payment_for_callback(request, payment_id=payment_id)
        if payment is None:
            return redirect_to_frontend_payment_result(payment_status='failed')

        if payment.status == Payment.STATUS_SUCCESS and payment.booking.status == Booking.STATUS_CONFIRMED:
            return redirect_to_frontend_payment_result(payment=payment, payment_status='success')

        try:
            verification_payload = verify_esewa_payment(payment)
        except ValueError as exc:
            if payment.status != Payment.STATUS_SUCCESS:
                payment = process_failed_payment(
                    payment,
                    provider_reference=get_esewa_provider_reference(callback_payload),
                    provider_response={
                        **(payment.provider_response or {}),
                        'gateway': 'esewa',
                        'callback': callback_payload,
                        'error': str(exc),
                    },
                )
            return redirect_to_frontend_payment_result(payment=payment, payment_status='failed')

        provider_reference = get_esewa_provider_reference(callback_payload, verification_payload)
        provider_response = {
            **(payment.provider_response or {}),
            'gateway': 'esewa',
            'callback': callback_payload,
            'verification': verification_payload,
        }

        if is_esewa_verification_complete(verification_payload):
            payment, _, capacity_error = process_successful_payment(
                payment,
                provider_reference=provider_reference,
                provider_response=provider_response,
            )
            if capacity_error:
                return redirect_to_frontend_payment_result(payment=payment, payment_status='failed')
            return redirect_to_frontend_payment_result(payment=payment, payment_status='success')

        if payment.status != Payment.STATUS_SUCCESS:
            payment = process_failed_payment(
                payment,
                provider_reference=provider_reference,
                provider_response=provider_response,
            )
        return redirect_to_frontend_payment_result(payment=payment, payment_status='failed')


class EsewaFailureView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, payment_id=None):
        return self._handle(request, payment_id=payment_id)

    def post(self, request, payment_id=None):
        return self._handle(request, payment_id=payment_id)

    def _handle(self, request, payment_id=None):
        payment, callback_payload = get_esewa_payment_for_callback(request, payment_id=payment_id)

        if payment is not None and payment.status != Payment.STATUS_SUCCESS:
            payment = process_failed_payment(
                payment,
                provider_reference=get_esewa_provider_reference(callback_payload),
                provider_response={
                    **(payment.provider_response or {}),
                    'gateway': 'esewa',
                    'callback': callback_payload,
                    'status': 'FAILED_REDIRECT',
                },
            )

        return redirect_to_frontend_payment_result(payment=payment, payment_status='failed')


class OfflineBookingView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = OfflineBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, created_user = get_or_create_offline_user(
            serializer.validated_data['user_email'],
            serializer.validated_data.get('username', ''),
        )
        event = serializer.validated_data['event']

        eligibility_error = get_booking_validation_error(user, event)
        if eligibility_error:
            return Response(eligibility_error, status=status.HTTP_400_BAD_REQUEST)

        booking = create_pending_booking(user, event, booking_source=Booking.SOURCE_OFFLINE)

        provider = Payment.PROVIDER_CASH if booking.total_price > 0 else Payment.PROVIDER_FREE
        method = 'CASH' if booking.total_price > 0 else 'FREE'
        payment = create_payment_for_booking(
            booking,
            provider=provider,
            method=method,
            status=Payment.STATUS_SUCCESS,
        )
        payment, ticket, capacity_error = process_successful_payment(
            payment,
            provider_reference=build_payment_reference('WALKIN'),
            provider_response={'source': 'offline-booking'},
        )
        if capacity_error:
            return Response(
                {
                    'detail': capacity_error,
                    'booking': BookingSerializer(booking, context={'request': request}).data,
                    'payment': PaymentSerializer(payment).data,
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                'message': 'Walk-in booking confirmed successfully.',
                'created_user': created_user,
                'attendee_email': booking.user.email,
                'attendee_name': booking.user.username,
                'booking': BookingSerializer(booking, context={'request': request}).data,
                'payment': PaymentSerializer(payment).data,
                'ticket_code': ticket.ticket_code,
            },
            status=status.HTTP_201_CREATED,
        )


class TicketScanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TicketScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket = get_object_or_404(
            Ticket.objects.select_related(
                'booking',
                'booking__event',
                'booking__user',
                'checked_in_by',
            ),
            ticket_code=serializer.validated_data['ticket_code'],
        )

        permission = IsAdminOrEventOrganizer()
        if not permission.has_object_permission(request, self, ticket):
            return Response({'detail': 'You do not have permission to scan this ticket.'}, status=status.HTTP_403_FORBIDDEN)

        event = serializer.validated_data.get('event')
        if event and ticket.booking.event_id != event.id:
            return Response({'detail': 'Ticket does not belong to the selected event.'}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.validated_data['mark_checked_in']:
            if not ticket.mark_checked_in(request.user):
                return Response(
                    {
                        'detail': 'This ticket has already been scanned.',
                        'ticket': ticket.ticket_code,
                        'scanned_at': ticket.scanned_at,
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            message = 'Ticket checked in successfully.'
        else:
            message = 'Ticket is valid.'

        return Response(
            {
                'message': message,
                'ticket': {
                    'ticket_code': ticket.ticket_code,
                    'is_scanned': ticket.is_scanned,
                    'scanned_at': ticket.scanned_at,
                },
                'booking': BookingSerializer(ticket.booking, context={'request': request}).data,
            }
        )
