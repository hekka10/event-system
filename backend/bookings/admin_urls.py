from django.urls import path

from .views import OfflineBookingView


urlpatterns = [
    path('offline-booking/', OfflineBookingView.as_view(), name='admin_offline_booking'),
]
