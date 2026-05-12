from django.contrib import admin

from .models import (
    Announcement,
    AuditLog,
    BarangayProfile,
    BarangayOfficial,
    BlotterIncident,
    Certificate,
    Event,
    EventAttendee,
    EventResource,
    HealthRecord,
    Household,
    Project,
    Resident,
    ResidentNotification,
    Service,
    ServiceRequest,
)


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("household_number", "purok", "street_address", "contact_number")
    search_fields = ("household_number", "purok", "street_address")


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = (
        "last_name",
        "first_name",
        "gender",
        "civil_status",
        "voter_status",
        "household",
        "is_household_head",
    )
    list_filter = ("gender", "civil_status", "voter_status", "is_household_head")
    search_fields = ("first_name", "middle_name", "last_name", "contact_number")


@admin.register(BarangayOfficial)
class BarangayOfficialAdmin(admin.ModelAdmin):
    list_display = ("position", "full_name", "committee", "term_start", "term_end", "is_active")
    list_filter = ("is_active",)
    search_fields = ("position", "first_name", "last_name", "committee")
    ordering = ("display_order", "position")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "fee", "processing_days", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("request_number", "service", "applicant_display", "status", "requested_at")
    list_filter = ("status", "service")
    search_fields = ("request_number", "applicant_name", "resident__first_name", "resident__last_name")
    readonly_fields = ("request_number", "requested_at")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "certificate_type", "applicant_display", "status", "issued_on")
    list_filter = ("certificate_type", "status")
    search_fields = ("certificate_number", "applicant_name", "resident__first_name", "resident__last_name", "purpose")
    readonly_fields = ("certificate_number", "created_at")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "published_on", "is_published")
    list_filter = ("category", "is_published")
    search_fields = ("title", "body")


@admin.register(BlotterIncident)
class BlotterIncidentAdmin(admin.ModelAdmin):
    list_display = ("case_number", "incident_type", "complainant_name", "status", "incident_date")
    list_filter = ("status", "incident_type")
    search_fields = ("case_number", "complainant_name", "respondent_name", "incident_type")
    readonly_fields = ("case_number", "created_at", "updated_at")


class EventAttendeeInline(admin.TabularInline):
    model = EventAttendee
    extra = 0


class EventResourceInline(admin.TabularInline):
    model = EventResource
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "venue", "start_at", "status", "expected_attendees", "is_public")
    list_filter = ("category", "status", "is_public")
    search_fields = ("title", "venue", "organizer", "target_audience", "description")
    date_hierarchy = "start_at"
    inlines = (EventAttendeeInline, EventResourceInline)


@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    list_display = ("display_name", "event", "role", "status", "checked_in_at")
    list_filter = ("status", "role")
    search_fields = ("name", "resident__first_name", "resident__last_name", "event__title")


@admin.register(EventResource)
class EventResourceAdmin(admin.ModelAdmin):
    list_display = ("item", "quantity", "event", "assigned_to", "status")
    list_filter = ("status",)
    search_fields = ("item", "assigned_to", "event__title")


@admin.register(BarangayProfile)
class BarangayProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "province", "contact_number", "updated_at")


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ("display_name", "category", "record_date", "next_follow_up")
    list_filter = ("category",)
    search_fields = ("name", "resident__first_name", "resident__last_name", "details")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "budget", "funding_source", "lead_official")
    list_filter = ("status",)
    search_fields = ("title", "description", "funding_source")


@admin.register(ResidentNotification)
class ResidentNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "channel", "audience", "status", "scheduled_for", "created_at")
    list_filter = ("channel", "status")
    search_fields = ("title", "message", "audience")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "module", "action")
    list_filter = ("module",)
    search_fields = ("user", "module", "action", "details")
    readonly_fields = ("created_at",)
