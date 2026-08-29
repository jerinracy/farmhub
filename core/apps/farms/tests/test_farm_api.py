from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.farms.models import Farm

User = get_user_model()


class FarmAPITestCase(APITestCase):
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
        self.farmer = User.objects.create_user(
            username="farmer_test",
            email="farmer_test@farmhub.com",
            password="FarmerPassword123",
            role=User.Role.FARMER,
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

        self.list_url = "/api/farms/"
        self.farm_1_url = f"/api/farms/{self.farm_1.id}/"
        self.farm_2_url = f"/api/farms/{self.farm_2.id}/"

    def test_superadmin_can_create_farm_and_assign_agent(self):
        self.client.force_authenticate(user=self.superadmin)
        payload = {
            "name": "Riverdale Farm",
            "location": "Sylhet",
            "agent": self.agent_1.id,
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Riverdale Farm")
        self.assertEqual(response.data["agent"], self.agent_1.id)
        self.assertEqual(response.data["agent_detail"]["username"], "agent_1")
        self.assertEqual(response.data["created_by"], self.superadmin.id)

    def test_agent_cannot_create_farm(self):
        self.client.force_authenticate(user=self.agent_1)
        payload = {
            "name": "Unauthorized Farm",
            "location": "Dhaka",
            "agent": self.agent_1.id,
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_farmer_cannot_create_farm(self):
        self.client.force_authenticate(user=self.farmer)
        payload = {
            "name": "Farmer Attempted Farm",
            "location": "Khulna",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_agent_can_patch_their_own_farm(self):
        self.client.force_authenticate(user=self.agent_1)
        payload = {
            "location": "Gazipur Updated",
        }
        response = self.client.patch(self.farm_1_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.farm_1.refresh_from_db()
        self.assertEqual(self.farm_1.location, "Gazipur Updated")

    def test_agent_cannot_patch_another_agents_farm(self):
        self.client.force_authenticate(user=self.agent_1)
        payload = {
            "location": "Hacked Location",
        }
        response = self.client.patch(self.farm_2_url, payload, format="json")
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_superadmin_can_delete_farm(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.delete(self.farm_1_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Farm.objects.filter(id=self.farm_1.id).exists())

    def test_agent_cannot_delete_farm(self):
        self.client.force_authenticate(user=self.agent_1)
        response = self.client.delete(self.farm_1_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_queryset_filtering(self):
        # SuperAdmin sees all farms
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        farm_ids = [item["id"] for item in response.data]
        self.assertIn(self.farm_1.id, farm_ids)
        self.assertIn(self.farm_2.id, farm_ids)

        # Agent 1 sees only farm 1
        self.client.force_authenticate(user=self.agent_1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        farm_ids = [item["id"] for item in response.data]
        self.assertIn(self.farm_1.id, farm_ids)
        self.assertNotIn(self.farm_2.id, farm_ids)

        # Farmer currently sees no farms
        self.client.force_authenticate(user=self.farmer)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
