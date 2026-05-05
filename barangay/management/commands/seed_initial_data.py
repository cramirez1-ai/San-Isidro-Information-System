from django.core.management.base import BaseCommand
from django.utils import timezone

from barangay.models import Announcement, Service


class Command(BaseCommand):
    help = "Create starter services and a sample announcement for the barangay system."

    def handle(self, *args, **options):
        services = [
            {
                "name": "Barangay Clearance",
                "description": "Clearance issued for local transactions and identification support.",
                "requirements": "Valid ID\nProof of residence",
                "fee": 0,
                "processing_days": 1,
            },
            {
                "name": "Certificate of Residency",
                "description": "Certification that the applicant is a resident of Barangay San Isidro.",
                "requirements": "Valid ID\nHousehold information",
                "fee": 0,
                "processing_days": 1,
            },
            {
                "name": "Certificate of Indigency",
                "description": "Certification for residents requesting social service assistance.",
                "requirements": "Valid ID\nInterview or assessment record",
                "fee": 0,
                "processing_days": 1,
            },
            {
                "name": "Business Clearance",
                "description": "Barangay clearance for business registration or renewal.",
                "requirements": "Valid ID\nBusiness details\nLocation information",
                "fee": 0,
                "processing_days": 2,
            },
            {
                "name": "Blotter Report Copy",
                "description": "Certified copy of a recorded barangay blotter incident.",
                "requirements": "Valid ID\nCase number or incident details",
                "fee": 0,
                "processing_days": 1,
            },
        ]

        created_services = 0
        for service in services:
            _, created = Service.objects.get_or_create(
                name=service["name"],
                defaults=service,
            )
            created_services += int(created)

        _, announcement_created = Announcement.objects.get_or_create(
            title="Sample: Barangay Office Schedule",
            defaults={
                "category": Announcement.Category.ADVISORY,
                "body": "Barangay services are available during regular office hours. Update this sample announcement with the official schedule.",
                "published_on": timezone.localdate(),
                "is_published": True,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Starter data ready. Services added: {created_services}. "
                f"Announcement added: {int(announcement_created)}."
            )
        )
