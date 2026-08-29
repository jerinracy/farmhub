from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cattle.models import Cow
from apps.farmers.models import FarmerProfile
from apps.farms.models import Farm

User = get_user_model()


class CowAPITestCase(APITestCase):
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

        self.farmer_1 = User.objects.create_user(
            username="farmer_1",
            email="farmer1@farmhub.com",
            password="FarmerPassword123",
            role=User.Role.FARMER,
        )
        self.profile_1 = FarmerProfile.objects.create(
            user=self.farmer_1,
            farm=self.farm_1,
            onboarded_by=self.agent_1,
        )

        self.farmer_2 = User.objects.create_user(
            username="farmer_2",
            email="farmer2@farmhub.com",
            password="FarmerPassword123",
            role=User.Role.FARMER,
        )
        self.profile_2 = FarmerProfile.objects.create(
            user=self.farmer_2,
            farm=self.farm_2,
            onboarded_by=self.agent_2,
        )

        self.list_url = "/api/cows/"

    def test_farmer_enrolls_own_cow(self):
        self.client.force_authenticate(user=self.farmer_1)
        payload = {
            "tag_id": "COW-001",
            "breed": "Holstein Friesian",
            "gender": "F",
            "date_of_birth": "2024-01-15",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cow = Cow.objects.get(tag_id="COW-001")
        self.assertEqual(cow.farmer, self.farmer_1)
        self.assertEqual(cow.farm, self.farm_1)
        self.assertEqual(cow.breed, "Holstein Friesian")
        self.assertEqual(cow.gender, "F")
        self.assertTrue(cow.is_active)

    def test_farmer_cannot_enroll_cow_under_different_farmer(self):
        self.client.force_authenticate(user=self.farmer_1)
        payload = {
            "tag_id": "COW-002",
            "breed": "Jersey",
            "gender": "M",
            "farmer": self.farmer_2.id,  # Attempting to assign to farmer_2
            "farm": self.farm_2.id,      # Attempting to assign to farm_2
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cow = Cow.objects.get(tag_id="COW-002")
        # Should be forced to farmer_1 and farm_1
        self.assertEqual(cow.farmer, self.farmer_1)
        self.assertEqual(cow.farm, self.farm_1)

    def test_agent_enrolls_cow_for_managed_farmer(self):
        self.client.force_authenticate(user=self.agent_1)
        payload = {
            "tag_id": "COW-003",
            "breed": "Sahiwal",
            "gender": "F",
            "farmer": self.farmer_1.id,
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cow = Cow.objects.get(tag_id="COW-003")
        self.assertEqual(cow.farmer, self.farmer_1)
        self.assertEqual(cow.farm, self.farm_1)

    def test_agent_cannot_enroll_cow_for_unmanaged_farmer(self):
        self.client.force_authenticate(user=self.agent_1)
        payload = {
            "tag_id": "COW-004",
            "breed": "Red Chittagong",
            "gender": "F",
            "farmer": self.farmer_2.id,  # farmer_2 belongs to farm_2 (managed by agent_2)
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_duplicate_tag_id_returns_bad_request(self):
        Cow.objects.create(
            tag_id="COW-DUP",
            breed="Sindhi",
            gender="F",
            farmer=self.farmer_1,
            farm=self.farm_1,
        )

        self.client.force_authenticate(user=self.farmer_1)
        payload = {
            "tag_id": "COW-DUP",
            "breed": "Sindhi",
            "gender": "F",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tag_id", response.data)

    def test_cow_queryset_isolation(self):
        cow_1 = Cow.objects.create(
            tag_id="COW-ISO-1",
            breed="Local",
            gender="F",
            farmer=self.farmer_1,
            farm=self.farm_1,
        )
        cow_2 = Cow.objects.create(
            tag_id="COW-ISO-2",
            breed="Cross",
            gender="F",
            farmer=self.farmer_2,
            farm=self.farm_2,
        )

        # Farmer 1 sees only cow 1
        self.client.force_authenticate(user=self.farmer_1)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tags = [c["tag_id"] for c in res.data]
        self.assertIn("COW-ISO-1", tags)
        self.assertNotIn("COW-ISO-2", tags)

        # Agent 1 sees only cow 1
        self.client.force_authenticate(user=self.agent_1)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tags = [c["tag_id"] for c in res.data]
        self.assertIn("COW-ISO-1", tags)
        self.assertNotIn("COW-ISO-2", tags)

        # SuperAdmin sees both
        self.client.force_authenticate(user=self.superadmin)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tags = [c["tag_id"] for c in res.data]
        self.assertIn("COW-ISO-1", tags)
        self.assertIn("COW-ISO-2", tags)
