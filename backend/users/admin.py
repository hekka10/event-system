from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import StudentVerification, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('email', 'username', 'auth_provider', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username', 'google_sub')
    ordering = ('email',)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Authentication Provider', {'fields': ('auth_provider', 'google_sub')}),
    )


@admin.register(StudentVerification)
class StudentVerificationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'student_email',
        'institution_name',
        'status',
        'approved_by',
        'reviewed_at',
    )
    list_filter = ('status', 'institution_name')
    search_fields = ('user__email', 'student_email', 'student_id', 'institution_name')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at')
