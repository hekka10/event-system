from django.contrib import admin

from .models import Booking, Payment, Ticket


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'event',
        'status',
        'booking_source',
        'is_student',
        'total_price',
        'confirmed_at',
    )
    list_filter = ('status', 'booking_source', 'is_student')
    search_fields = ('user__email', 'event__title')
    readonly_fields = ('created_at', 'updated_at', 'confirmed_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'external_reference',
        'booking',
        'provider',
        'status',
        'amount',
        'paid_at',
    )
    list_filter = ('provider', 'status', 'currency')
    search_fields = ('external_reference', 'provider_reference', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'paid_at', 'verified_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_code', 'booking', 'is_scanned', 'scanned_at', 'checked_in_by')
    list_filter = ('is_scanned',)
    search_fields = ('ticket_code', 'booking__user__email', 'booking__event__title')
