from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum

from .models import Announcement, Attendee, BudgetItem, Department, Event, Resource, Venue, Volunteer, Feedback

# Admin Site Title
admin.site.site_header  = "Brgy San Isidro Administration"
admin.site.site_title   = "Brgy San Isidro Admin"
admin.site.index_title  = "Brgy San Isidro Surigao City, Surigao del Norte, Philippines"


class AttendeeInline(admin.TabularInline):
    model   = Attendee
    extra   = 0
    fields  = ("full_name", "purok", "role", "status", "checked_in_at")
    readonly_fields = ("checked_in_at",)

class ResourceInline(admin.TabularInline):
    model  = Resource
    extra  = 0
    fields = ("item", "quantity", "custodian", "status")

class BudgetItemInline(admin.TabularInline):
    model  = BudgetItem
    extra  = 0
    fields = ("item", "amount", "funding_source", "status")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "venue", "start_at", "status_badge", "expected_attendees", "total_budget_display", "is_public")
    list_filter   = ("category", "status", "is_public", "venue", "department")
    search_fields = ("title", "description", "organizer")
    date_hierarchy = "start_at"
    inlines       = (AttendeeInline, ResourceInline, BudgetItemInline)
    fieldsets = (
        ("Basic Information", {"fields": ("title", "category", "description", "venue", "department", "organizer")}),
        ("Schedule",          {"fields": ("start_at", "end_at", "target_audience", "expected_attendees")}),
        ("Status & Budget",   {"fields": ("status", "is_public", "budget_ceiling", "risk_notes")}),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "Planning":  ("#1d4ed8", "#eff6ff"),
            "Scheduled": ("#7c3aed", "#f5f3ff"),
            "Ongoing":   ("#15803d", "#f0fdf4"),
            "Completed": ("#5c6b62", "#edf6f0"),
            "Cancelled": ("#b91c1c", "#fef2f2"),
            "Draft":     ("#b45309", "#fffbeb"),
        }
        color, bg = colors.get(obj.status, ("#5c6b62", "#edf6f0"))
        return format_html('<span style="padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;background:{};color:{};">{}</span>', bg, color, obj.status)

    @admin.display(description="Total Budget")
    def total_budget_display(self, obj):
        total = obj.budget_items.aggregate(total=Sum("amount"))["total"] or 0
        return format_html("₱{:,.2f}", total)


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display  = ("name", "purok", "capacity", "manager", "active_badge")
    list_filter   = ("is_active", "purok")
    search_fields = ("name", "purok", "address", "manager")

    @admin.display(description="Active", boolean=True)
    def active_badge(self, obj):
        return obj.is_active


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ("name", "focal_person", "contact_number", "event_count")
    search_fields = ("name", "focal_person")

    @admin.display(description="Events")
    def event_count(self, obj):
        return format_html('<strong style="color:#15803d;">{}</strong>', obj.events.count())


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display  = ("full_name", "event", "purok", "role", "status_badge", "checked_in_at")
    list_filter   = ("status", "role", "event")
    search_fields = ("full_name", "purok", "event__title")

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "Invited":   ("#b45309", "#fffbeb"),
            "Confirmed": ("#1d4ed8", "#eff6ff"),
            "Attended":  ("#15803d", "#f0fdf4"),
            "Absent":    ("#b91c1c", "#fef2f2"),
        }
        color, bg = colors.get(obj.status, ("#5c6b62", "#edf6f0"))
        return format_html('<span style="padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;background:{};color:{};">{}</span>', bg, color, obj.status)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display  = ("item", "quantity", "event", "custodian", "status_badge")
    list_filter   = ("status", "event")
    search_fields = ("item", "custodian", "event__title")

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "Needed":    ("#b91c1c", "#fef2f2"),
            "Requested": ("#b45309", "#fffbeb"),
            "Reserved":  ("#1d4ed8", "#eff6ff"),
            "Ready":     ("#15803d", "#f0fdf4"),
            "Returned":  ("#5c6b62", "#edf6f0"),
        }
        color, bg = colors.get(obj.status, ("#5c6b62", "#edf6f0"))
        return format_html('<span style="padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;background:{};color:{};">{}</span>', bg, color, obj.status)


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display  = ("item", "event", "amount_display", "funding_source", "status_badge")
    list_filter   = ("status", "funding_source")
    search_fields = ("item", "event__title")

    @admin.display(description="Amount")
    def amount_display(self, obj):
        return format_html("₱{:,.2f}", obj.amount)

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "Planned":    ("#b45309", "#fffbeb"),
            "Approved":   ("#1d4ed8", "#eff6ff"),
            "Released":   ("#7c3aed", "#f5f3ff"),
            "Liquidated": ("#15803d", "#f0fdf4"),
        }
        color, bg = colors.get(obj.status, ("#5c6b62", "#edf6f0"))
        return format_html('<span style="padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;background:{};color:{};">{}</span>', bg, color, obj.status)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display  = ("title", "category", "event", "published_on", "published_badge")
    list_filter   = ("category", "is_published")
    search_fields = ("title", "body")
    date_hierarchy = "published_on"

    @admin.display(description="Published", boolean=True)
    def published_badge(self, obj):
        return obj.is_published


@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display  = ("full_name", "event", "purok", "role", "status_badge")
    list_filter   = ("status", "event")
    search_fields = ("full_name", "purok", "event__title")

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "Registered": ("#b45309", "#fffbeb"),
            "Confirmed":  ("#1d4ed8", "#eff6ff"),
            "Attended":   ("#15803d", "#f0fdf4"),
            "Absent":     ("#b91c1c", "#fef2f2"),
        }
        color, bg = colors.get(obj.status, ("#5c6b62", "#edf6f0"))
        return format_html('<span style="padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;background:{};color:{};">{}</span>', bg, color, obj.status)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display  = ("event", "respondent_name", "rating", "submitted_at")
    list_filter   = ("rating", "event")
    search_fields = ("respondent_name", "comments", "event__title")
