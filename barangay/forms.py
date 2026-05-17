from django import forms

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


class DateInput(forms.DateInput):
    input_type = "date"


class TimeInput(forms.TimeInput):
    input_type = "time"


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class StyledModelForm(StyledFormMixin, forms.ModelForm):
    pass


class HouseholdForm(StyledModelForm):
    class Meta:
        model = Household
        fields = ["household_number", "purok", "street_address", "contact_number", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class ResidentForm(StyledModelForm):
    class Meta:
        model = Resident
        fields = [
            "household",
            "first_name",
            "middle_name",
            "last_name",
            "suffix",
            "gender",
            "date_of_birth",
            "civil_status",
            "voter_status",
            "occupation",
            "contact_number",
            "address",
            "is_household_head",
            "remarks",
        ]
        widgets = {
            "date_of_birth": DateInput(),
            "remarks": forms.Textarea(attrs={"rows": 3}),
        }


class BarangayOfficialForm(StyledModelForm):
    class Meta:
        model = BarangayOfficial
        fields = [
            "position",
            "first_name",
            "last_name",
            "committee",
            "contact_number",
            "term_start",
            "term_end",
            "display_order",
            "is_active",
        ]
        widgets = {
            "term_start": DateInput(),
            "term_end": DateInput(),
        }


class ServiceForm(StyledModelForm):
    class Meta:
        model = Service
        fields = ["name", "description", "requirements", "fee", "processing_days", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "requirements": forms.Textarea(attrs={"rows": 3}),
        }


class ServiceRequestForm(StyledModelForm):
    class Meta:
        model = ServiceRequest
        fields = [
            "service",
            "resident",
            "applicant_name",
            "purpose",
            "status",
            "target_release",
            "released_at",
            "notes",
        ]
        widgets = {
            "target_release": DateInput(),
            "released_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("resident") and not cleaned.get("applicant_name"):
            self.add_error("applicant_name", "Enter an applicant name if no resident is selected.")
        return cleaned


class CertificateForm(StyledModelForm):
    class Meta:
        model = Certificate
        fields = [
            "certificate_type",
            "resident",
            "applicant_name",
            "purpose",
            "status",
            "issued_on",
            "valid_until",
            "remarks",
        ]
        widgets = {
            "issued_on": DateInput(),
            "valid_until": DateInput(),
            "remarks": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("resident") and not cleaned.get("applicant_name"):
            self.add_error("applicant_name", "Enter an applicant name if no resident is selected.")
        return cleaned


class AnnouncementForm(StyledModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "category", "body", "published_on", "is_published"]
        widgets = {
            "published_on": DateInput(),
            "body": forms.Textarea(attrs={"rows": 5}),
        }


class BlotterIncidentForm(StyledModelForm):
    class Meta:
        model = BlotterIncident
        fields = [
            "complainant_name",
            "respondent_name",
            "incident_type",
            "incident_date",
            "incident_time",
            "location",
            "description",
            "action_taken",
            "status",
        ]
        widgets = {
            "incident_date": DateInput(),
            "incident_time": TimeInput(),
            "description": forms.Textarea(attrs={"rows": 4}),
            "action_taken": forms.Textarea(attrs={"rows": 3}),
        }


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%dT%H:%M")
        super().__init__(*args, **kwargs)


class EventForm(StyledModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "category",
            "description",
            "venue",
            "start_at",
            "end_at",
            "organizer",
            "lead_official",
            "target_audience",
            "expected_attendees",
            "budget",
            "status",
            "is_public",
            "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "start_at": DateTimeInput(),
            "end_at": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")
        if start_at and end_at and end_at <= start_at:
            self.add_error("end_at", "End time must be after the start time.")
        return cleaned


class EventAttendeeForm(StyledModelForm):
    class Meta:
        model = EventAttendee
        fields = ["event", "resident", "name", "contact_number", "role", "status", "checked_in_at", "notes"]
        widgets = {
            "checked_in_at": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("resident") and not cleaned.get("name"):
            self.add_error("name", "Enter a name if no resident is selected.")
        return cleaned


class EventResourceForm(StyledModelForm):
    class Meta:
        model = EventResource
        fields = ["event", "item", "quantity", "assigned_to", "status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class BarangayProfileForm(StyledModelForm):
    class Meta:
        model = BarangayProfile
        fields = [
            "name",
            "city",
            "province",
            "region",
            "classification",
            "psgc_code",
            "correspondence_code",
            "population_2020",
            "postal_code",
            "contact_number",
            "email",
            "address",
        ]


class HealthRecordForm(StyledModelForm):
    class Meta:
        model = HealthRecord
        fields = ["resident", "name", "category", "record_date", "details", "next_follow_up"]
        widgets = {
            "record_date": DateInput(),
            "next_follow_up": DateInput(),
            "details": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("resident") and not cleaned.get("name"):
            self.add_error("name", "Enter a name if no resident is selected.")
        return cleaned


class ProjectForm(StyledModelForm):
    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "budget",
            "funding_source",
            "start_date",
            "end_date",
            "status",
            "lead_official",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "start_date": DateInput(),
            "end_date": DateInput(),
        }


class ResidentNotificationForm(StyledModelForm):
    class Meta:
        model = ResidentNotification
        fields = ["title", "message", "channel", "audience", "status", "scheduled_for"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
            "scheduled_for": DateTimeInput(),
        }
