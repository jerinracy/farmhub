from rest_framework.permissions import BasePermission

from .models import User


class IsSuperAdmin(BasePermission):
    """
    Allows access only to SuperAdmin users or superusers.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, "role", None) == User.Role.SUPERADMIN
                or request.user.is_superuser
            )
        )


class IsAgent(BasePermission):
    """
    Allows access only to Agent users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == User.Role.AGENT
        )


class IsFarmer(BasePermission):
    """
    Allows access only to Farmer users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == User.Role.FARMER
        )
