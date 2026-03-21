from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BookingViewSet,
    OfflineBookingView,
    PaymentDetailView,
    PaymentInitiationView,
    PaymentVerificationView,
    PaymentWebhookView,
    TicketScanView,
)

router = DefaultRouter()
router.register(r'', BookingViewSet, basename='booking')

urlpatterns = [
    path('initiate-payment/', PaymentInitiationView.as_view(), name='payment_initiate'),
    path('payments/<uuid:payment_id>/', PaymentDetailView.as_view(), name='payment_detail'),
    path(
        'payments/<uuid:payment_id>/verify/',
        PaymentVerificationView.as_view(),
        name='payment_verify',
    ),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment_webhook'),
    path('offline/', OfflineBookingView.as_view(), name='offline_booking'),
    path('tickets/scan/', TicketScanView.as_view(), name='ticket_scan'),
    path('', include(router.urls)),
]
