from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class AuthJWTEndpointsTestCase(APITestCase):
    def setUp(self):
        self.password = "SuperSecurePass123"
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@farmhub.com",
            password=self.password,
            role=User.Role.SUPERADMIN,
            phone_number="1234567890",
        )
        self.login_url = reverse("accounts:login")
        self.refresh_url = reverse("accounts:refresh")
        self.logout_url = reverse("accounts:logout")

    def test_login_returns_tokens_and_custom_claims(self):
        payload = {
            "username": self.user.username,
            "password": self.password,
        }
        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # Check response body contains access, refresh, role, username, id
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["id"], self.user.id)
        self.assertEqual(data["username"], self.user.username)
        self.assertEqual(data["role"], self.user.role)

        # Check JWT access token payload contains claims
        access_token = AccessToken(data["access"])
        self.assertEqual(access_token["id"], self.user.id)
        self.assertEqual(access_token["username"], self.user.username)
        self.assertEqual(access_token["role"], self.user.role)

    def test_login_invalid_credentials(self):
        payload = {
            "username": self.user.username,
            "password": "wrongpassword",
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        login_response = self.client.post(
            self.login_url,
            {"username": self.user.username, "password": self.password},
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            self.refresh_url,
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_logout_blacklists_refresh_token(self):
        login_response = self.client.post(
            self.login_url,
            {"username": self.user.username, "password": self.password},
            format="json",
        )
        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        # Logout with auth header and refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_response = self.client.post(
            self.logout_url,
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(logout_response.data["detail"], "Successfully logged out.")

        # Attempting to refresh with the blacklisted token should fail
        refresh_response = self.client.post(
            self.refresh_url,
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
