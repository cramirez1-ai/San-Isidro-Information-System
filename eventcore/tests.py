from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Attendee, Event, Venue


class EventCoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="clerk", password="StrongPass123!")
        self.venue = Venue.objects.create(name="Barangay Hall", capacity=100)
        self.event = Event.objects.create(
            title="Health Mission",
            category=Event.Category.HEALTH,
            venue=self.venue,
            start_at=timezone.now() + timedelta(days=1),
            end_at=timezone.now() + timedelta(days=1, hours=3),
            status=Event.Status.SCHEDULED,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("eventcore:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_loads_for_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("eventcore:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Event Command Center")

    def test_event_list_and_detail_load(self):
        self.client.force_login(self.user)
        list_response = self.client.get(reverse("eventcore:event_list"))
        detail_response = self.client.get(reverse("eventcore:event_detail", args=[self.event.pk]))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Health Mission")

    def test_confirmed_count(self):
        Attendee.objects.create(event=self.event, full_name="Ana Santos", status=Attendee.Status.CONFIRMED)
        self.assertEqual(self.event.confirmed_count, 1)

    def test_calendar_uses_sunday_first_dates(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("eventcore:calendar"), {"year": 2026, "month": 5})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "May 2026")
        first_week = response.context["calendar_days"][:7]
        self.assertEqual([day["day"] for day in first_week], ["", "", "", "", "", 1, 2])
