from rest_framework import permissions


class IsAdminOrEventOrganizer(permissions.BasePermission):
    """
    Allow access to admin users and the organizer of the related event.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        event = getattr(obj, 'event', None)
        if event is None and hasattr(obj, 'booking'):
            event = getattr(obj.booking, 'event', None)

        return bool(
            user.is_staff
            or user.is_superuser
            or (event is not None and event.organizer_id == user.id)
        )
