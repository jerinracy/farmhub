from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cattle.models import Cow
from apps.farmers.models import FarmerProfile
from apps.farms.models import Farm
from apps.production.models import MilkProduction

User = get_user_model()


class MilkProductionAPITestCase(APITestCase):
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

        self.cow_1 = Cow.objects.create(
            tag_id="COW-MILK-1",
            breed="Holstein",
            gender="F",
            farmer=self.farmer_1,
            farm=self.farm_1,
        )
        self.cow_2 = Cow.objects.create(
            tag_id="COW-MILK-2",
            breed="Jersey",
            gender="F",
            farmer=self.farmer_2,
            farm=self.farm_2,
        )

        self.cow_1_records_url = f"/api/cows/{self.cow_1.id}/milk-records/"
        self.cow_2_records_url = f"/api/cows/{self.cow_2.id}/milk-records/"

    def test_farmer_records_morning_milk_for_own_cow(self):
        self.client.force_authenticate(user=self.farmer_1)
        payload = {
            "date": "2026-08-25",
            "quantity_liters": "14.50",
            "session": "MORNING",
        }
        response = self.client.post(self.cow_1_records_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        record = MilkProduction.objects.get(id=response.data["id"])
        self.assertEqual(record.cow, self.cow_1)
        self.assertEqual(record.farm, self.farm_1)
        self.assertEqual(record.farmer, self.farmer_1)
        self.assertEqual(float(record.quantity_liters), 14.50)
        self.assertEqual(record.session, "MORNING")

    def test_duplicate_cow_date_session_returns_400(self):
        MilkProduction.objects.create(
            cow=self.cow_1,
            farm=self.farm_1,
            farmer=self.farmer_1,
            date="2026-08-25",
            quantity_liters="12.00",
            session="MORNING",
        )

        self.client.force_authenticate(user=self.farmer_1)
        payload = {
            "date": "2026-08-25",
            "quantity_liters": "15.00",
            "session": "MORNING",
        }
        response = self.client.post(self.cow_1_records_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_agent_records_milk_for_managed_farm_cow(self):
        self.client.force_authenticate(user=self.agent_1)
        payload = {
            "date": "2026-08-25",
            "quantity_liters": "10.25",
            "session": "EVENING",
        }
        response = self.client.post(self.cow_1_records_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        record = MilkProduction.objects.get(id=response.data["id"])
        self.assertEqual(record.cow, self.cow_1)
        self.assertEqual(record.farmer, self.farmer_1)
        self.assertEqual(record.farm, self.farm_1)

    def test_farmer_cannot_record_milk_for_another_farmers_cow(self):
        self.client.force_authenticate(user=self.farmer_1)
        payload = {
            "date": "2026-08-25",
            "quantity_liters": "11.00",
            "session": "MORNING",
        }
        # Attempt to access cow_2 which belongs to farmer_2
        response = self.client.post(self.cow_2_records_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
