from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from eventcore.models import Announcement, Attendee, BudgetItem, Department, Event, Resource, Venue


class Command(BaseCommand):
    help = "Create starter EventCore data for Barangay San Isidro."

    def handle(self, *args, **options):
        departments = [
            ("Health and Sanitation", "BHW Coordinator"),
            ("Disaster Risk Reduction", "BDRRMC Focal"),
            ("Youth and Sports", "SK Chairperson"),
            ("Environment", "Clean and Green Lead"),
        ]
        department_objects = {}
        for name, focal in departments:
            department_objects[name], _ = Department.objects.get_or_create(
                name=name,
                defaults={"focal_person": focal, "description": f"{name} event coordination team."},
            )

        venues = [
            ("Barangay San Isidro Hall", "Purok 1", 120),
            ("San Isidro Covered Court", "Purok 2", 350),
            ("Barangay Plaza", "Purok 3", 500),
            ("Riverside Purok Center", "Purok 4", 90),
        ]
        venue_objects = {}
        for name, purok, capacity in venues:
            venue_objects[name], _ = Venue.objects.get_or_create(
                name=name,
                defaults={"purok": purok, "capacity": capacity, "manager": "Barangay Office"},
            )

        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        event, event_created = Event.objects.get_or_create(
            title="Barangay San Isidro Community Clean-up Drive",
            defaults={
                "category": Event.Category.CLEANUP,
                "description": "Community clean-up and coastal care activity for residents and youth volunteers.",
                "venue": venue_objects["Barangay Plaza"],
                "department": department_objects["Environment"],
                "organizer": "Barangay San Isidro Council",
                "start_at": now + timedelta(days=7),
                "end_at": now + timedelta(days=7, hours=4),
                "target_audience": "Residents, youth volunteers, purok leaders",
                "expected_attendees": 120,
                "budget_ceiling": 8500,
                "status": Event.Status.SCHEDULED,
                "risk_notes": "Prepare drinking water, gloves, first aid, and rain contingency.",
            },
        )

        if event_created:
            attendees = [
                ("Maria Santos", "Purok 1", "Purok Leader", Attendee.Status.CONFIRMED),
                ("Jose Ramirez", "Purok 2", "Volunteer", Attendee.Status.CONFIRMED),
                ("Ana Dela Cruz", "Purok 3", "BHW Support", Attendee.Status.INVITED),
            ]
            for full_name, purok, role, status in attendees:
                Attendee.objects.create(event=event, full_name=full_name, purok=purok, role=role, status=status)

            resources = [
                ("Trash sacks", 100, "Environment team", Resource.Status.READY),
                ("Gloves", 80, "Barangay Office", Resource.Status.RESERVED),
                ("First aid kit", 2, "BHW Coordinator", Resource.Status.READY),
                ("Sound system", 1, "SK Council", Resource.Status.REQUESTED),
            ]
            for item, quantity, custodian, status in resources:
                Resource.objects.create(event=event, item=item, quantity=quantity, custodian=custodian, status=status)

            budgets = [
                ("Drinking water", 1800, "Barangay fund", BudgetItem.Status.APPROVED),
                ("Cleaning supplies", 3200, "Barangay fund", BudgetItem.Status.APPROVED),
                ("Snacks for volunteers", 3500, "Donation / partner support", BudgetItem.Status.PLANNED),
            ]
            for item, amount, source, status in budgets:
                BudgetItem.objects.create(event=event, item=item, amount=amount, funding_source=source, status=status)

        Announcement.objects.get_or_create(
            title="Community Clean-up Drive Schedule",
            defaults={
                "category": Announcement.Category.EVENT,
                "event": event,
                "body": "Residents and volunteers are invited to join the Barangay San Isidro clean-up drive. Please coordinate with your purok leader.",
                "published_on": timezone.localdate(),
                "is_published": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("EventCore starter data is ready."))
