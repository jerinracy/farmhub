from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import User

from .models import FarmerProfile
from .permissions import IsSuperAdminOrManagingAgent
from .serializers import (
    FarmerListSerializer,
    FarmerOnboardSerializer,
    FarmerUpdateSerializer,
)


class FarmerViewSet(ModelViewSet):
    """
    CRUD ViewSet for Farmer Onboarding and Profile Management.
    """

    queryset = FarmerProfile.objects.all()
    permission_classes = [IsAuthenticated, IsSuperAdminOrManagingAgent]

    def get_serializer_class(self):
        if self.action == "create":
            return FarmerOnboardSerializer
        if self.action in ["update", "partial_update"]:
            return FarmerUpdateSerializer
        return FarmerListSerializer

    def get_queryset(self):
        user = self.request.user
        if not (user and user.is_authenticated):
            return FarmerProfile.objects.none()

        base_queryset = FarmerProfile.objects.select_related(
            "user",
            "farm",
            "onboarded_by",
        ).order_by("-joined_at")

        if getattr(user, "role", None) == User.Role.SUPERADMIN or user.is_superuser:
            return base_queryset

        if getattr(user, "role", None) == User.Role.AGENT:
            return base_queryset.filter(farm__agent=user)

        if getattr(user, "role", None) == User.Role.FARMER:
            return base_queryset.filter(user=user)

        return FarmerProfile.objects.none()
