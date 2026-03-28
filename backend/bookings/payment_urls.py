from django.urls import path

from .views import (
    PaymentDetailView,
    PaymentInitiationView,
    PaymentVerificationRequestView,
    PaymentWebhookView,
)


urlpatterns = [
    path('initiate/', PaymentInitiationView.as_view(), name='payments_initiate'),
    path('verify/', PaymentVerificationRequestView.as_view(), name='payments_verify'),
    path('webhook/', PaymentWebhookView.as_view(), name='payments_webhook'),
    path('<uuid:payment_id>/', PaymentDetailView.as_view(), name='payments_detail'),
]
