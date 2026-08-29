from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import User

from .models import Farm
from .permissions import IsSuperAdminOrOwningAgent
from .serializers import FarmSerializer


class FarmViewSet(ModelViewSet):
    """
    CRUD ViewSet for managing Farms.
    """

    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrOwningAgent]

    def get_queryset(self):
        user = self.request.user
        if not (user and user.is_authenticated):
            return Farm.objects.none()

        if getattr(user, "role", None) == User.Role.SUPERADMIN or user.is_superuser:
            return (
                Farm.objects.all()
                .select_related("agent", "created_by")
                .order_by("-created_at")
            )

        if getattr(user, "role", None) == User.Role.AGENT:
            return (
                Farm.objects.filter(agent=user)
                .select_related("agent", "created_by")
                .order_by("-created_at")
            )

        if getattr(user, "role", None) == User.Role.FARMER:
            if hasattr(user, "farmer_profile") and user.farmer_profile.farm_id:
                return (
                    Farm.objects.filter(id=user.farmer_profile.farm_id)
                    .select_related("agent", "created_by")
                    .order_by("-created_at")
                )
            return Farm.objects.none()

        return Farm.objects.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
