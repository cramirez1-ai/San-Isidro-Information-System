from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import BlotterIncident, Household, Resident, Service, ServiceRequest


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="barangay_user",
            email="user@example.com",
            password="StrongPass123!",
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_dashboard_loads(self):
        response = self.client.get(reverse("barangay:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Barangay San Isidro")

    def test_add_url_aliases_load(self):
        add_urls = [
            "households/add/",
            "residents/add/",
            "officials/add/",
            "services/add/",
            "requests/add/",
            "announcements/add/",
            "blotter/add/",
        ]
        for url in add_urls:
            with self.subTest(url=url):
                response = self.client.get(f"/{url}")
                self.assertEqual(response.status_code, 200)

    def test_household_list_shows_registry_summary(self):
        household = Household.objects.create(
            household_number="HH-001",
            purok="Purok 1",
            street_address="Riverside Road",
        )
        Resident.objects.create(
            household=household,
            first_name="Ana",
            last_name="Santos",
            gender=Resident.Gender.FEMALE,
            is_household_head=True,
        )

        response = self.client.get(reverse("barangay:household_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1 household shown")
        self.assertContains(response, "Linked Members")
        self.assertContains(response, "HH-001")


class UserAuthTests(TestCase):
    def test_dashboard_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse("barangay:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("barangay:login"), response["Location"])

    def test_auth_pages_load(self):
        urls = [
            reverse("barangay:login"),
            reverse("barangay:password_reset"),
            reverse("barangay:password_reset_done"),
            reverse("barangay:password_reset_complete"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_regular_users_cannot_open_admin_workspace(self):
        user = User.objects.create_user(
            username="clerk",
            email="clerk@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("barangay:dashboard"))

        self.assertEqual(response.status_code, 403)


class RecordNumberTests(TestCase):
    def test_service_request_number_is_generated(self):
        service = Service.objects.create(name="Barangay Clearance")
        request = ServiceRequest.objects.create(
            service=service,
            applicant_name="Test Applicant",
            purpose="Employment",
        )
        self.assertTrue(request.request_number.startswith("SIS-"))

    def test_blotter_case_number_is_generated(self):
        incident = BlotterIncident.objects.create(
            complainant_name="Test Complainant",
            incident_type="Noise complaint",
            incident_date=timezone.localdate(),
            description="Test description",
        )
        self.assertTrue(incident.case_number.startswith("BLT-"))
