from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import User
from apps.cattle.models import Cow
from .models import MilkProduction
from .serializers import MilkProductionSerializer


class MilkProductionViewSet(ModelViewSet):
    """
    ViewSet for managing Milk Production records nested under /api/cows/{cow_pk}/milk-records/
    """

    queryset = MilkProduction.objects.all()
    serializer_class = MilkProductionSerializer
    permission_classes = [IsAuthenticated]

    def get_cow(self):
        cow_pk = self.kwargs.get("cow_pk")
        user = self.request.user
        if not (user and user.is_authenticated):
            raise Http404

        if getattr(user, "role", None) == User.Role.SUPERADMIN or user.is_superuser:
            cow_qs = Cow.objects.all()
        elif getattr(user, "role", None) == User.Role.AGENT:
            cow_qs = Cow.objects.filter(farm__agent=user)
        elif getattr(user, "role", None) == User.Role.FARMER:
            cow_qs = Cow.objects.filter(farmer=user)
        else:
            cow_qs = Cow.objects.none()

        try:
            return cow_qs.get(pk=cow_pk)
        except Cow.DoesNotExist:
            raise Http404("Cow not found or not accessible.")

    def get_queryset(self):
        cow = self.get_cow()
        return (
            MilkProduction.objects.filter(cow=cow)
            .select_related("cow", "farm", "farmer")
            .order_by("-date", "-recorded_at")
        )

    def perform_create(self, serializer):
        cow = self.get_cow()
        serializer.save(
            cow=cow,
            farm=cow.farm,
            farmer=cow.farmer,
        )
