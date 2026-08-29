from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import User


class IsSuperAdminOrOwningAgent(BasePermission):
    """
    Permission class for Farm management:
    - SuperAdmin can create, list, retrieve, update, and delete any farm.
    - Agent can view and update only farms where farm.agent == request.user.
    - Others cannot create, update, or delete farms.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        is_superadmin = (
            getattr(request.user, "role", None) == User.Role.SUPERADMIN
            or request.user.is_superuser
        )

        # Only SuperAdmin can create or delete
        if view.action in ["create", "destroy"]:
            return is_superadmin

        # List, retrieve, update, partial_update
        return True

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        is_superadmin = (
            getattr(request.user, "role", None) == User.Role.SUPERADMIN
            or request.user.is_superuser
        )
        if is_superadmin:
            return True

        is_agent = getattr(request.user, "role", None) == User.Role.AGENT
        if is_agent and obj.agent == request.user:
            if view.action in ["retrieve", "update", "partial_update"] or request.method in SAFE_METHODS:
                return True

        return False
