from django.conf import settings
from django.shortcuts import get_object_or_404
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
    PaymentVerificationSerializer,
    PaymentWebhookSerializer,
    TicketScanSerializer,
)
from .services import (
    build_payment_reference,
    create_pending_booking,
    create_payment_for_booking,
    get_booking_validation_error,
    get_or_create_offline_user,
    process_failed_payment,
    process_successful_payment,
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

        payment = create_payment_for_booking(booking, provider=Payment.PROVIDER_MOCK, method='ONLINE')
        return Response(
            {
                'message': 'Payment initiated successfully.',
                'next_action': 'COMPLETE_PAYMENT',
                'booking': BookingSerializer(booking, context={'request': request}).data,
                'payment': PaymentSerializer(payment).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, payment_id):
        payment = get_object_or_404(
            Payment.objects.select_related('booking', 'booking__event', 'user'),
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


class PaymentVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        payment = get_object_or_404(
            Payment.objects.select_related('booking', 'booking__event', 'user'),
            pk=payment_id,
        )

        if not (request.user.is_staff or payment.user_id == request.user.id):
            return Response({'detail': 'You do not have permission to verify this payment.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PaymentVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data['status'] == Payment.STATUS_SUCCESS:
            payment, _, capacity_error = process_successful_payment(
                payment,
                provider_reference=serializer.validated_data.get('provider_reference', ''),
                provider_response=serializer.validated_data.get('provider_response'),
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
                provider_reference=serializer.validated_data.get('provider_reference', ''),
                provider_response=serializer.validated_data.get('provider_response'),
            )

        return Response(
            {
                'message': 'Payment verification completed.',
                'booking': BookingSerializer(payment.booking, context={'request': request}).data,
                'payment': PaymentSerializer(payment).data,
            }
        )


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


class OfflineBookingView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = OfflineBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, _ = get_or_create_offline_user(
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
