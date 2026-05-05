from django.contrib import admin

from .models import (
    Announcement,
    BarangayOfficial,
    BlotterIncident,
    Household,
    Resident,
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
