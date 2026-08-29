from django.urls import path

from .views import MilkProductionViewSet

app_name = "production"

urlpatterns = [
    path(
        "",
        MilkProductionViewSet.as_view({"get": "list", "post": "create"}),
        name="milk-record-list",
    ),
    path(
        "<int:pk>/",
        MilkProductionViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="milk-record-detail",
    ),
]
