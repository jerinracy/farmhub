from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import User
from apps.cattle.models import Cow

from .models import CowActivity
from .serializers import CowActivitySerializer


class CowActivityViewSet(ModelViewSet):
    """
    ViewSet for managing Cow Activities nested under /api/cows/{cow_pk}/activities/
    """

    queryset = CowActivity.objects.all()
    serializer_class = CowActivitySerializer
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
            CowActivity.objects.filter(cow=cow)
            .select_related("cow", "recorded_by")
            .order_by("-date", "-created_at")
        )

    def perform_create(self, serializer):
        cow = self.get_cow()
        serializer.save(
            cow=cow,
            recorded_by=self.request.user,
        )
