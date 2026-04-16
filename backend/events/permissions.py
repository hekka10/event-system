from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow everyone to read, but reserve writes for admins.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsOrganizerOrAdmin(permissions.BasePermission):
    """
    Allow event edits only for the organizer or an admin user.
    """

    def has_permission(self, request, view):
        if getattr(view, "action", None) == "attendees":
            return bool(request.user and request.user.is_authenticated)

        if request.method in permissions.SAFE_METHODS:
            return True

        if getattr(view, "action", None) in ["update", "partial_update", "destroy"]:
            return request.user and request.user.is_authenticated

        return True

    def has_object_permission(self, request, view, obj):
        if getattr(view, "action", None) == "attendees":
            user = request.user
            if not user or not user.is_authenticated:
                return False
            return user.is_staff or user.is_superuser or obj.organizer_id == user.id

        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        return user.is_staff or user.is_superuser or obj.organizer_id == user.id
