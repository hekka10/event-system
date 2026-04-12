from django.urls import path

from .views import (
    EsewaFailureView,
    EsewaSuccessView,
    PaymentDetailView,
    PaymentInitiationView,
    PaymentRetryView,
    PaymentVerificationRequestView,
    PaymentWebhookView,
)


urlpatterns = [
    path('initiate/', PaymentInitiationView.as_view(), name='payments_initiate'),
    path('verify/', PaymentVerificationRequestView.as_view(), name='payments_verify'),
    path('webhook/', PaymentWebhookView.as_view(), name='payments_webhook'),
    path('esewa/success/<uuid:payment_id>/', EsewaSuccessView.as_view(), name='esewa_success'),
    path('esewa/failure/<uuid:payment_id>/', EsewaFailureView.as_view(), name='esewa_failure'),
    path('esewa/success/', EsewaSuccessView.as_view(), name='esewa_success_legacy'),
    path('esewa/failure/', EsewaFailureView.as_view(), name='esewa_failure_legacy'),
    path('<uuid:payment_id>/retry/', PaymentRetryView.as_view(), name='payments_retry'),
    path('<uuid:payment_id>/', PaymentDetailView.as_view(), name='payments_detail'),
]
