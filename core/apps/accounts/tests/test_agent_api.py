from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AgentManagementAPITestCase(APITestCase):
    def setUp(self):
        self.superadmin = User.objects.create_user(
            username="superadmin_test",
            email="superadmin_test@farmhub.com",
            password="AdminPassword123",
            role=User.Role.SUPERADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.agent = User.objects.create_user(
            username="agent_test",
            email="agent_test@farmhub.com",
            password="AgentPassword123",
            role=User.Role.AGENT,
            phone_number="01700000000",
            created_by=self.superadmin,
        )
        self.farmer = User.objects.create_user(
            username="farmer_test",
            email="farmer_test@farmhub.com",
            password="FarmerPassword123",
            role=User.Role.FARMER,
            phone_number="01800000000",
        )
        self.list_url = "/api/agents/"
        self.detail_url = f"/api/agents/{self.agent.id}/"
        self.login_url = reverse("accounts:login")

    def test_superadmin_can_create_agent(self):
        self.client.force_authenticate(user=self.superadmin)
        payload = {
            "username": "new_agent",
            "email": "new_agent@farmhub.com",
            "password": "NewAgentPassword123",
            "phone_number": "01911112222",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_agent = User.objects.get(username="new_agent")
        self.assertEqual(created_agent.role, User.Role.AGENT)
        self.assertTrue(created_agent.is_active)
        self.assertEqual(created_agent.created_by, self.superadmin)
        self.assertEqual(created_agent.phone_number, "01911112222")

        # Confirm new agent can authenticate and log in
        self.client.force_authenticate(user=None)
        login_response = self.client.post(
            self.login_url,
            {
                "username": "new_agent",
                "password": "NewAgentPassword123",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data["role"], "AGENT")

    def test_agent_cannot_create_agent(self):
        self.client.force_authenticate(user=self.agent)
        payload = {
            "username": "another_agent",
            "email": "another_agent@farmhub.com",
            "password": "Password123",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_farmer_cannot_create_agent(self):
        self.client.force_authenticate(user=self.farmer)
        payload = {
            "username": "another_agent_2",
            "email": "another_agent_2@farmhub.com",
            "password": "Password123",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_access_agents(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_superadmin_can_list_agents_only(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [item["username"] for item in response.data]
        self.assertIn("agent_test", usernames)
        self.assertNotIn("superadmin_test", usernames)
        self.assertNotIn("farmer_test", usernames)

    def test_superadmin_can_retrieve_agent(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "agent_test")
        self.assertEqual(response.data["role"], "AGENT")

    def test_superadmin_can_update_agent(self):
        self.client.force_authenticate(user=self.superadmin)
        payload = {
            "phone_number": "01799999999",
        }
        response = self.client.patch(self.detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.agent.refresh_from_db()
        self.assertEqual(self.agent.phone_number, "01799999999")

    def test_superadmin_can_deactivate_agent(self):
        self.client.force_authenticate(user=self.superadmin)
        payload = {
            "is_active": False,
        }
        response = self.client.patch(self.detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.agent.refresh_from_db()
        self.assertFalse(self.agent.is_active)
