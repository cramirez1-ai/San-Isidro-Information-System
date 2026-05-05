from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    Announcement,
    BarangayOfficial,
    BlotterIncident,
    Household,
    Resident,
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


class UserRegistrationForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email


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
