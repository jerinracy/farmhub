from django.urls import path

from .views import CustomTokenObtainPairView, LogoutView, MeView, TokenRefreshView

app_name = "accounts"


urlpatterns = [
    path(
        "login/",
        CustomTokenObtainPairView.as_view(),
        name="login",
    ),
    path(
        "refresh/",
        TokenRefreshView.as_view(),
        name="refresh",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "me/",
        MeView.as_view(),
        name="me",
    ),
]
