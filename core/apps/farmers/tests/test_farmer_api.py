from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.farmers.models import FarmerProfile
from apps.farms.models import Farm

User = get_user_model()


class FarmerOnboardingAPITestCase(APITestCase):
    def setUp(self):
        self.superadmin = User.objects.create_user(
            username="superadmin_test",
            email="superadmin_test@farmhub.com",
            password="AdminPassword123",
            role=User.Role.SUPERADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.agent_1 = User.objects.create_user(
            username="agent_1",
            email="agent_1@farmhub.com",
            password="AgentPassword123",
            role=User.Role.AGENT,
            phone_number="01711111111",
        )
        self.agent_2 = User.objects.create_user(
            username="agent_2",
            email="agent_2@farmhub.com",
            password="AgentPassword123",
            role=User.Role.AGENT,
            phone_number="01722222222",
        )
        self.farm_1 = Farm.objects.create(
            name="Green Valley Farm",
            location="Gazipur",
            agent=self.agent_1,
            created_by=self.superadmin,
        )
        self.farm_2 = Farm.objects.create(
            name="Sunrise Dairy Farm",
            location="Bogura",
            agent=self.agent_2,
            created_by=self.superadmin,
        )

        self.list_url = "/api/farmers/"
        self.login_url = reverse("accounts:login")

    def test_superadmin_can_onboard_farmer_onto_any_farm(self):
        self.client.force_authenticate(user=self.superadmin)
        payload = {
            "username": "farmer_karim",
            "email": "karim@farmhub.com",
            "password": "KarimPassword123!",
            "phone_number": "01733333333",
            "farm": self.farm_2.id,
            "national_id": "NID-123456789",
            "address": "Bogura Sadar",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="farmer_karim")
        self.assertEqual(user.role, User.Role.FARMER)
        self.assertEqual(user.phone_number, "01733333333")

        profile = FarmerProfile.objects.get(user=user)
        self.assertEqual(profile.farm, self.farm_2)
        self.assertEqual(profile.national_id, "NID-123456789")
        self.assertEqual(profile.address, "Bogura Sadar")
        self.assertEqual(profile.onboarded_by, self.superadmin)

        # Confirm new farmer can log in
        self.client.force_authenticate(user=None)
        login_response = self.client.post(
            self.login_url,
            {
                "username": "farmer_karim",
                "password": "KarimPassword123!",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data["role"], "FARMER")

    def test_agent_can_onboard_farmer_onto_own_managed_farm(self):
        self.client.force_authenticate(user=self.agent_1)
        payload = {
            "username": "farmer_rahim",
            "email": "rahim@farmhub.com",
            "password": "RahimPassword123!",
            "phone_number": "01744444444",
            "farm": self.farm_1.id,
            "national_id": "NID-987654321",
            "address": "Gazipur Chowrasta",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="farmer_rahim")
        self.assertEqual(user.role, User.Role.FARMER)
        profile = FarmerProfile.objects.get(user=user)
        self.assertEqual(profile.farm, self.farm_1)
        self.assertEqual(profile.onboarded_by, self.agent_1)

    def test_agent_cannot_onboard_farmer_onto_another_agents_farm(self):
        self.client.force_authenticate(user=self.agent_1)
        payload = {
            "username": "farmer_hacked",
            "email": "hacked@farmhub.com",
            "password": "Password123!",
            "farm": self.farm_2.id,  # Managed by agent_2
            "national_id": "NID-000000",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("farm", response.data)

    def test_farmer_cannot_onboard_other_farmers(self):
        # Create an existing farmer
        farmer_user = User.objects.create_user(
            username="existing_farmer",
            email="existing_farmer@farmhub.com",
            password="Password123!",
            role=User.Role.FARMER,
        )
        FarmerProfile.objects.create(
            user=farmer_user,
            farm=self.farm_1,
        )

        self.client.force_authenticate(user=farmer_user)
        payload = {
            "username": "sub_farmer",
            "email": "sub@farmhub.com",
            "password": "Password123!",
            "farm": self.farm_1.id,
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_farmer_sees_own_farm_in_farms_endpoint(self):
        farmer_user = User.objects.create_user(
            username="farm_viewer_farmer",
            email="viewer@farmhub.com",
            password="Password123!",
            role=User.Role.FARMER,
        )
        FarmerProfile.objects.create(
            user=farmer_user,
            farm=self.farm_1,
        )

        self.client.force_authenticate(user=farmer_user)
        response = self.client.get("/api/farms/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.farm_1.id)
        self.assertEqual(response.data[0]["name"], "Green Valley Farm")
