from django.contrib import admin

from .models import Category, Event


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'date',
        'location',
        'organizer',
        'price',
        'capacity',
        'is_approved',
    )
    list_filter = ('is_approved', 'category')
    search_fields = ('title', 'location', 'organizer__email')
    readonly_fields = ('created_at', 'updated_at')
