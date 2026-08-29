from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsSuperAdminOrManagingAgentOrCowFarmer(BasePermission):
    """
    Permission class for Cow management:
    - SuperAdmin can create, list, retrieve, update, delete all cows.
    - Agent can create, list, retrieve, update cows on farms they manage.
    - Farmer can create, list, retrieve, update their own cows.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        user = request.user
        if getattr(user, "role", None) == User.Role.SUPERADMIN or user.is_superuser:
            return True

        if getattr(user, "role", None) == User.Role.AGENT:
            return obj.farm.agent == user

        if getattr(user, "role", None) == User.Role.FARMER:
            return obj.farmer == user

        return False
