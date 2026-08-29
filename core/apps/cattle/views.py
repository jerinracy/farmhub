from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import User

from .models import Cow
from .permissions import IsSuperAdminOrManagingAgentOrCowFarmer
from .serializers import CowSerializer


class CowViewSet(ModelViewSet):
    """
    CRUD ViewSet for Cow management and enrollment.
    """

    queryset = Cow.objects.all()
    serializer_class = CowSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrManagingAgentOrCowFarmer]

    def get_queryset(self):
        user = self.request.user
        if not (user and user.is_authenticated):
            return Cow.objects.none()

        base_queryset = Cow.objects.select_related(
            "farm",
            "farmer",
            "farm__agent",
        ).order_by("-created_at")

        if getattr(user, "role", None) == User.Role.SUPERADMIN or user.is_superuser:
            return base_queryset

        if getattr(user, "role", None) == User.Role.AGENT:
            return base_queryset.filter(farm__agent=user)

        if getattr(user, "role", None) == User.Role.FARMER:
            return base_queryset.filter(farmer=user)

        return Cow.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if getattr(user, "role", None) == User.Role.FARMER:
            farm = user.farmer_profile.farm
            serializer.save(farmer=user, farm=farm)
        else:
            serializer.save()
