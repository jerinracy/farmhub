from django.urls import path

from .views import CowActivityViewSet

app_name = "activities"

urlpatterns = [
    path(
        "",
        CowActivityViewSet.as_view({"get": "list", "post": "create"}),
        name="cow-activity-list",
    ),
    path(
        "<int:pk>/",
        CowActivityViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="cow-activity-detail",
    ),
]
