from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.activities.models import CowActivity
from apps.cattle.models import Cow
from apps.farmers.models import FarmerProfile
from apps.farms.models import Farm

User = get_user_model()


class CowActivityAPITestCase(APITestCase):
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
            tag_id="COW-ACT-1",
            breed="Holstein",
            gender="F",
            farmer=self.farmer_1,
            farm=self.farm_1,
        )
        self.cow_2 = Cow.objects.create(
            tag_id="COW-ACT-2",
            breed="Jersey",
            gender="F",
            farmer=self.farmer_2,
            farm=self.farm_2,
        )

        self.cow_1_activities_url = f"/api/cows/{self.cow_1.id}/activities/"
        self.cow_2_activities_url = f"/api/cows/{self.cow_2.id}/activities/"

    def test_farmer_logs_vaccination_for_own_cow(self):
        self.client.force_authenticate(user=self.farmer_1)
        payload = {
            "activity_type": "VACCINATION",
            "date": "2026-08-20",
            "notes": "Anthrax vaccine administered",
            "details": {
                "vaccine_name": "BioAnthrax",
                "dosage_ml": 2.5,
            },
        }
        response = self.client.post(self.cow_1_activities_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        activity = CowActivity.objects.get(id=response.data["id"])
        self.assertEqual(activity.cow, self.cow_1)
        self.assertEqual(activity.activity_type, "VACCINATION")
        self.assertEqual(str(activity.date), "2026-08-20")
        self.assertEqual(activity.details["vaccine_name"], "BioAnthrax")
        self.assertEqual(activity.recorded_by, self.farmer_1)

    def test_farmer_cannot_log_activity_for_another_farmers_cow(self):
        self.client.force_authenticate(user=self.farmer_1)
        payload = {
            "activity_type": "HEALTH_CHECK",
            "date": "2026-08-21",
            "notes": "Unauthorized health check attempt",
        }
        # Attempt to access cow_2 which belongs to farmer_2
        response = self.client.post(self.cow_2_activities_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_agent_logs_health_check_for_cow_on_managed_farm(self):
        self.client.force_authenticate(user=self.agent_1)
        payload = {
            "activity_type": "HEALTH_CHECK",
            "date": "2026-08-22",
            "notes": "Routine checkup: Normal temperature and weight.",
            "details": {"temperature_f": 101.5, "weight_kg": 420},
        }
        response = self.client.post(self.cow_1_activities_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        activity = CowActivity.objects.get(id=response.data["id"])
        self.assertEqual(activity.cow, self.cow_1)
        self.assertEqual(activity.recorded_by, self.agent_1)

    def test_agent_cannot_log_activity_for_unmanaged_cow(self):
        self.client.force_authenticate(user=self.agent_1)
        payload = {
            "activity_type": "HEALTH_CHECK",
            "date": "2026-08-22",
        }
        # cow_2 belongs to farm_2 (managed by agent_2)
        response = self.client.post(self.cow_2_activities_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_activities_ordered_by_descending_date(self):
        CowActivity.objects.create(
            cow=self.cow_1,
            activity_type="VACCINATION",
            date="2026-08-10",
            notes="First",
            recorded_by=self.farmer_1,
        )
        CowActivity.objects.create(
            cow=self.cow_1,
            activity_type="HEALTH_CHECK",
            date="2026-08-25",
            notes="Latest",
            recorded_by=self.farmer_1,
        )
        CowActivity.objects.create(
            cow=self.cow_1,
            activity_type="BIRTH",
            date="2026-08-18",
            notes="Middle",
            recorded_by=self.farmer_1,
        )

        self.client.force_authenticate(user=self.farmer_1)
        response = self.client.get(self.cow_1_activities_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        dates = [item["date"] for item in response.data]
        self.assertEqual(dates, ["2026-08-25", "2026-08-18", "2026-08-10"])
