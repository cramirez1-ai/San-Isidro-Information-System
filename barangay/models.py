from django.db import models
from django.urls import reverse
from django.utils import timezone


class BarangayProfile(models.Model):
    name = models.CharField(max_length=160, default="Barangay San Isidro")
    city = models.CharField(max_length=120, default="Surigao City")
    province = models.CharField(max_length=120, default="Surigao del Norte")
    region = models.CharField(max_length=120, default="Caraga")
    classification = models.CharField(max_length=120, default="Rural barangay")
    psgc_code = models.CharField(max_length=30, blank=True)
    correspondence_code = models.CharField(max_length=30, blank=True)
    population_2020 = models.PositiveIntegerField(default=629)
    postal_code = models.CharField(max_length=20, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Barangay Profile"
        verbose_name_plural = "Barangay Profile"

    def __str__(self):
        return self.name

    @classmethod
    def current(cls):
        profile, _ = cls.objects.get_or_create(pk=1)
        return profile


class Household(models.Model):
    household_number = models.CharField(max_length=30, unique=True)
    purok = models.CharField(max_length=80)
    street_address = models.CharField(max_length=255, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["household_number"]

    def __str__(self):
        return f"Household {self.household_number}"

    @property
    def head(self):
        if "residents" in getattr(self, "_prefetched_objects_cache", {}):
            return next(
                (resident for resident in self.residents.all() if resident.is_household_head),
                None,
            )
        return self.residents.filter(is_household_head=True).first()


class Resident(models.Model):
    class Gender(models.TextChoices):
        FEMALE = "Female", "Female"
        MALE = "Male", "Male"
        OTHER = "Other", "Other"

    class CivilStatus(models.TextChoices):
        SINGLE = "Single", "Single"
        MARRIED = "Married", "Married"
        WIDOWED = "Widowed", "Widowed"
        SEPARATED = "Separated", "Separated"

    class VoterStatus(models.TextChoices):
        REGISTERED = "Registered", "Registered"
        NOT_REGISTERED = "Not Registered", "Not Registered"
        TRANSFERRED = "Transferred", "Transferred"
        UNKNOWN = "Unknown", "Unknown"

    household = models.ForeignKey(
        Household,
        related_name="residents",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    first_name = models.CharField(max_length=80)
    middle_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80)
    suffix = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices)
    date_of_birth = models.DateField(null=True, blank=True)
    civil_status = models.CharField(
        max_length=20,
        choices=CivilStatus.choices,
        default=CivilStatus.SINGLE,
    )
    voter_status = models.CharField(
        max_length=20,
        choices=VoterStatus.choices,
        default=VoterStatus.UNKNOWN,
    )
    occupation = models.CharField(max_length=120, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    is_household_head = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse("barangay:resident_detail", args=[self.pk])

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name, self.suffix]
        return " ".join(part for part in parts if part).strip()

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )


class BarangayOfficial(models.Model):
    position = models.CharField(max_length=100)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    committee = models.CharField(max_length=150, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    term_start = models.DateField(null=True, blank=True)
    term_end = models.DateField(null=True, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "position", "last_name"]

    def __str__(self):
        return f"{self.position} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Service(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    processing_days = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ServiceRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        PROCESSING = "Processing", "Processing"
        READY = "Ready", "Ready"
        RELEASED = "Released", "Released"
        CANCELLED = "Cancelled", "Cancelled"

    request_number = models.CharField(max_length=30, unique=True, blank=True)
    service = models.ForeignKey(Service, related_name="requests", on_delete=models.PROTECT)
    resident = models.ForeignKey(
        Resident,
        related_name="service_requests",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    applicant_name = models.CharField(max_length=160, blank=True)
    purpose = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    target_release = models.DateField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return self.request_number or f"Request for {self.service}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            today = timezone.localdate()
            prefix = f"SIS-{today:%Y%m%d}"
            next_number = ServiceRequest.objects.filter(
                request_number__startswith=prefix
            ).count() + 1
            candidate = f"{prefix}-{next_number:04d}"
            while ServiceRequest.objects.filter(request_number=candidate).exists():
                next_number += 1
                candidate = f"{prefix}-{next_number:04d}"
            self.request_number = candidate
        super().save(*args, **kwargs)

    @property
    def applicant_display(self):
        return self.resident.full_name if self.resident else self.applicant_name


class Certificate(models.Model):
    class CertificateType(models.TextChoices):
        CLEARANCE = "Barangay Clearance", "Barangay Clearance"
        INDIGENCY = "Certificate of Indigency", "Certificate of Indigency"
        RESIDENCY = "Certificate of Residency", "Certificate of Residency"
        BUSINESS = "Business Clearance", "Business Clearance"

    class Status(models.TextChoices):
        DRAFT = "Draft", "Draft"
        ISSUED = "Issued", "Issued"
        CLAIMED = "Claimed", "Claimed"
        CANCELLED = "Cancelled", "Cancelled"

    certificate_number = models.CharField(max_length=30, unique=True, blank=True)
    certificate_type = models.CharField(
        max_length=40,
        choices=CertificateType.choices,
        default=CertificateType.CLEARANCE,
    )
    resident = models.ForeignKey(
        Resident,
        related_name="certificates",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    applicant_name = models.CharField(max_length=160, blank=True)
    purpose = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    issued_on = models.DateField(default=timezone.localdate)
    valid_until = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_on", "-created_at"]

    def __str__(self):
        return self.certificate_number or self.certificate_type

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            today = timezone.localdate()
            prefix = f"CERT-{today:%Y%m%d}"
            next_number = Certificate.objects.filter(
                certificate_number__startswith=prefix
            ).count() + 1
            candidate = f"{prefix}-{next_number:04d}"
            while Certificate.objects.filter(certificate_number=candidate).exists():
                next_number += 1
                candidate = f"{prefix}-{next_number:04d}"
            self.certificate_number = candidate
        super().save(*args, **kwargs)

    @property
    def applicant_display(self):
        return self.resident.full_name if self.resident else self.applicant_name


class Announcement(models.Model):
    class Category(models.TextChoices):
        ADVISORY = "Advisory", "Advisory"
        PROGRAM = "Program", "Program"
        HEALTH = "Health", "Health"
        MEETING = "Meeting", "Meeting"
        EMERGENCY = "Emergency", "Emergency"

    title = models.CharField(max_length=160)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.ADVISORY,
    )
    body = models.TextField()
    published_on = models.DateField(default=timezone.localdate)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_on", "-created_at"]

    def __str__(self):
        return self.title


class Event(models.Model):
    class Category(models.TextChoices):
        ASSEMBLY = "Assembly", "Assembly"
        HEALTH = "Health", "Health"
        LIVELIHOOD = "Livelihood", "Livelihood"
        YOUTH = "Youth", "Youth"
        CLEANUP = "Clean-up", "Clean-up"
        RELIEF = "Relief", "Relief"
        CULTURAL = "Cultural", "Cultural"
        OTHER = "Other", "Other"

    class Status(models.TextChoices):
        PLANNING = "Planning", "Planning"
        SCHEDULED = "Scheduled", "Scheduled"
        ONGOING = "Ongoing", "Ongoing"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"

    title = models.CharField(max_length=180)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.ASSEMBLY)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=180, default="Barangay San Isidro")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    organizer = models.CharField(max_length=160, blank=True)
    lead_official = models.ForeignKey(
        BarangayOfficial,
        related_name="led_events",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    target_audience = models.CharField(max_length=180, blank=True)
    expected_attendees = models.PositiveIntegerField(default=0)
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)
    is_public = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at", "title"]

    def __str__(self):
        return self.title

    @property
    def duration_label(self):
        if not self.start_at or not self.end_at:
            return ""
        delta = self.end_at - self.start_at
        hours = max(delta.total_seconds() / 3600, 0)
        if hours < 1:
            return "Less than 1 hour"
        if hours == 1:
            return "1 hour"
        return f"{hours:g} hours"

    @property
    def attendance_total(self):
        return self.attendees.count()


class EventAttendee(models.Model):
    class AttendanceStatus(models.TextChoices):
        INVITED = "Invited", "Invited"
        CONFIRMED = "Confirmed", "Confirmed"
        ATTENDED = "Attended", "Attended"
        ABSENT = "Absent", "Absent"

    event = models.ForeignKey(Event, related_name="attendees", on_delete=models.CASCADE)
    resident = models.ForeignKey(
        Resident,
        related_name="event_attendances",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=160, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=80, default="Participant")
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.INVITED,
    )
    checked_in_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["event", "role", "name"]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.resident.full_name if self.resident else self.name


class EventResource(models.Model):
    class ResourceStatus(models.TextChoices):
        NEEDED = "Needed", "Needed"
        REQUESTED = "Requested", "Requested"
        RESERVED = "Reserved", "Reserved"
        READY = "Ready", "Ready"
        RETURNED = "Returned", "Returned"

    event = models.ForeignKey(Event, related_name="resources", on_delete=models.CASCADE)
    item = models.CharField(max_length=140)
    quantity = models.PositiveIntegerField(default=1)
    assigned_to = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ResourceStatus.choices,
        default=ResourceStatus.NEEDED,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["event", "item"]

    def __str__(self):
        return f"{self.quantity} x {self.item}"


class BlotterIncident(models.Model):
    class Status(models.TextChoices):
        OPEN = "Open", "Open"
        MEDIATION = "For Mediation", "For Mediation"
        SETTLED = "Settled", "Settled"
        REFERRED = "Referred", "Referred"
        CLOSED = "Closed", "Closed"

    case_number = models.CharField(max_length=30, unique=True, blank=True)
    complainant_name = models.CharField(max_length=160)
    respondent_name = models.CharField(max_length=160, blank=True)
    incident_type = models.CharField(max_length=120)
    incident_date = models.DateField()
    incident_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=180, blank=True)
    description = models.TextField()
    action_taken = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-incident_date", "-created_at"]

    def __str__(self):
        return self.case_number or self.incident_type

    def save(self, *args, **kwargs):
        if not self.case_number:
            year = timezone.localdate().year
            prefix = f"BLT-{year}"
            next_number = BlotterIncident.objects.filter(
                case_number__startswith=prefix
            ).count() + 1
            candidate = f"{prefix}-{next_number:04d}"
            while BlotterIncident.objects.filter(case_number=candidate).exists():
                next_number += 1
                candidate = f"{prefix}-{next_number:04d}"
            self.case_number = candidate
        super().save(*args, **kwargs)


class HealthRecord(models.Model):
    class Category(models.TextChoices):
        VACCINATION = "Vaccination", "Vaccination"
        MEDICAL_MISSION = "Medical Mission", "Medical Mission"
        SENIOR = "Senior Citizen", "Senior Citizen"
        PWD = "PWD", "PWD"
        OTHER = "Other", "Other"

    resident = models.ForeignKey(
        Resident,
        related_name="health_records",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=160, blank=True)
    category = models.CharField(max_length=30, choices=Category.choices)
    record_date = models.DateField(default=timezone.localdate)
    details = models.TextField(blank=True)
    next_follow_up = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-record_date", "category"]

    def __str__(self):
        return f"{self.display_name} - {self.category}"

    @property
    def display_name(self):
        return self.resident.full_name if self.resident else self.name


class Project(models.Model):
    class Status(models.TextChoices):
        PLANNING = "Planning", "Planning"
        ONGOING = "Ongoing", "Ongoing"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"

    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    funding_source = models.CharField(max_length=160, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)
    lead_official = models.ForeignKey(
        BarangayOfficial,
        related_name="projects",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["status", "title"]

    def __str__(self):
        return self.title


class ResidentNotification(models.Model):
    class Channel(models.TextChoices):
        SMS = "SMS", "SMS"
        EMAIL = "Email", "Email"
        POSTED = "Posted", "Posted"

    class Status(models.TextChoices):
        DRAFT = "Draft", "Draft"
        READY = "Ready", "Ready"
        SENT = "Sent", "Sent"

    title = models.CharField(max_length=160)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.POSTED)
    audience = models.CharField(max_length=160, default="All residents")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class AuditLog(models.Model):
    user = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=160)
    module = models.CharField(max_length=80, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} - {self.user or 'System'}"
