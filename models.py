from django.db import models
from django.urls import reverse
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    focal_person = models.CharField(max_length=120, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=140, unique=True)
    purok = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=220, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    manager = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Event(models.Model):

    class Category(models.TextChoices):
        ASSEMBLY = "Assembly", "Assembly"
        HEALTH = "Health", "Health"
        LIVELIHOOD = "Livelihood", "Livelihood"
        EDUCATION = "Education", "Education"
        YOUTH = "Youth", "Youth"
        CLEANUP = "Clean-up", "Clean-up"
        RELIEF = "Relief", "Relief"
        CULTURAL = "Cultural", "Cultural"
        SECURITY = "Security", "Security"
        OTHER = "Other", "Other"

    class Status(models.TextChoices):
        DRAFT = "Draft", "Draft"
        PLANNING = "Planning", "Planning"
        SCHEDULED = "Scheduled", "Scheduled"
        ONGOING = "Ongoing", "Ongoing"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"

    class ApprovalStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        REJECTED = "Rejected", "Rejected"

    title = models.CharField(max_length=180)
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.ASSEMBLY,
    )
    description = models.TextField(blank=True)
    venue = models.ForeignKey(
        Venue,
        related_name="events",
        on_delete=models.PROTECT,
    )
    department = models.ForeignKey(
        Department,
        related_name="events",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    organizer = models.CharField(max_length=140, default="Barangay San Isidro Council")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    target_audience = models.CharField(max_length=180, blank=True)
    expected_attendees = models.PositiveIntegerField(default=0)
    budget_ceiling = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNING,
    )
    is_public = models.BooleanField(default=True)
    risk_notes = models.TextField(blank=True)
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    approval_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("eventcore:event_detail", args=[self.pk])

    @property
    def is_upcoming(self):
        return self.end_at >= timezone.now() and self.status != self.Status.CANCELLED

    @property
    def confirmed_count(self):
        return self.attendees.filter(
            status__in=[Attendee.Status.CONFIRMED, Attendee.Status.ATTENDED]
        ).count()

    @property
    def total_budget(self):
        total = self.budget_items.aggregate(total=models.Sum("amount"))["total"]
        return total or 0

    @property
    def ready_resources(self):
        return self.resources.filter(
            status__in=[Resource.Status.READY, Resource.Status.RETURNED]
        ).count()


class Attendee(models.Model):

    class Status(models.TextChoices):
        INVITED = "Invited", "Invited"
        CONFIRMED = "Confirmed", "Confirmed"
        ATTENDED = "Attended", "Attended"
        ABSENT = "Absent", "Absent"

    event = models.ForeignKey(Event, related_name="attendees", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=160)
    purok = models.CharField(max_length=80, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=80, default="Participant")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INVITED,
    )
    checked_in_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["event", "role", "full_name"]

    def __str__(self):
        return self.full_name


class Resource(models.Model):

    class Status(models.TextChoices):
        NEEDED = "Needed", "Needed"
        REQUESTED = "Requested", "Requested"
        RESERVED = "Reserved", "Reserved"
        READY = "Ready", "Ready"
        RETURNED = "Returned", "Returned"

    event = models.ForeignKey(Event, related_name="resources", on_delete=models.CASCADE)
    item = models.CharField(max_length=140)
    quantity = models.PositiveIntegerField(default=1)
    custodian = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEEDED,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["event", "item"]

    def __str__(self):
        return f"{self.quantity} x {self.item}"


class BudgetItem(models.Model):

    class Status(models.TextChoices):
        PLANNED = "Planned", "Planned"
        APPROVED = "Approved", "Approved"
        RELEASED = "Released", "Released"
        LIQUIDATED = "Liquidated", "Liquidated"

    event = models.ForeignKey(Event, related_name="budget_items", on_delete=models.CASCADE)
    item = models.CharField(max_length=140)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    funding_source = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["event", "item"]

    def __str__(self):
        return f"{self.item} - {self.amount}"


class Announcement(models.Model):

    class Category(models.TextChoices):
        ADVISORY = "Advisory", "Advisory"
        EVENT = "Event", "Event"
        HEALTH = "Health", "Health"
        EMERGENCY = "Emergency", "Emergency"
        MEETING = "Meeting", "Meeting"

    title = models.CharField(max_length=160)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.EVENT,
    )
    event = models.ForeignKey(
        Event,
        related_name="announcements",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    body = models.TextField()
    published_on = models.DateField(default=timezone.localdate)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_on", "-created_at"]

    def __str__(self):
        return self.title
