from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import User


class IsSuperAdminOrManagingAgent(BasePermission):
    """
    Permission class for Farmer management:
    - SuperAdmin and Agent can create farmers.
    - SuperAdmin can view, update, delete all farmers.
    - Agent can view, update, delete farmers belonging to farms they manage.
    - Farmer can only view their own profile.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        is_superadmin = (
            getattr(request.user, "role", None) == User.Role.SUPERADMIN
            or request.user.is_superuser
        )
        is_agent = getattr(request.user, "role", None) == User.Role.AGENT
        is_farmer = getattr(request.user, "role", None) == User.Role.FARMER

        if view.action in ["create", "destroy"]:
            return is_superadmin or is_agent

        return is_superadmin or is_agent or is_farmer

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
        if is_agent:
            return obj.farm.agent == request.user

        is_farmer = getattr(request.user, "role", None) == User.Role.FARMER
        if is_farmer:
            if view.action in ["retrieve"] or request.method in SAFE_METHODS:
                return obj.user == request.user
            return False

        return False
