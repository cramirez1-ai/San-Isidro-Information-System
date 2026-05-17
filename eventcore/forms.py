from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Announcement, Attendee, BudgetItem, Department, Event, Resource, Venue
from .models import Announcement, Attendee, BudgetItem, Department, Event, Resource, Venue, Volunteer
from .models import Announcement, Attendee, BudgetItem, Department, Event, Feedback, Resource, Venue, Volunteer

class StyledMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class DateInput(forms.DateInput):
    input_type = "date"


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%dT%H:%M")
        super().__init__(*args, **kwargs)


class RegisterForm(StyledMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class EventForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "category",
            "description",
            "venue",
            "department",
            "organizer",
            "start_at",
            "end_at",
            "target_audience",
            "expected_attendees",
            "budget_ceiling",
            "status",
            "is_public",
            "risk_notes",
            "is_recurring",
            "recurrence",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "start_at": DateTimeInput(),
            "end_at": DateTimeInput(),
            "risk_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")
        venue = cleaned.get("venue")

        # Basic time validation
        if start_at and end_at and end_at <= start_at:
            self.add_error("end_at", "End time must be after start time.")

        # ✅ VENUE CONFLICT CHECKING
        if venue and start_at and end_at:
            conflicts = Event.objects.filter(
                venue=venue,
                start_at__lt=end_at,
                end_at__gt=start_at,
            ).exclude(status=Event.Status.CANCELLED)

            # Exclude current event if editing
            if self.instance and self.instance.pk:
                conflicts = conflicts.exclude(pk=self.instance.pk)

            if conflicts.exists():
                conflict = conflicts.first()
                self.add_error(
                    "venue",
                    f"Venue conflict! '{venue.name}' is already booked for "
                    f"'{conflict.title}' from "
                    f"{conflict.start_at.strftime('%b %d, %Y %I:%M %p')} to "
                    f"{conflict.end_at.strftime('%I:%M %p')}."
                )

        return cleaned


class AttendeeForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Attendee
        fields = ["event", "full_name", "purok", "contact_number", "role", "status", "checked_in_at", "notes"]
        widgets = {"checked_in_at": DateTimeInput(), "notes": forms.Textarea(attrs={"rows": 3})}


class ResourceForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Resource
        fields = ["event", "item", "quantity", "custodian", "status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class BudgetItemForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = BudgetItem
        fields = ["event", "item", "amount", "funding_source", "status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class AnnouncementForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "category", "event", "body", "published_on", "is_published"]
        widgets = {"published_on": DateInput(), "body": forms.Textarea(attrs={"rows": 5})}


class VenueForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Venue
        fields = ["name", "purok", "address", "capacity", "manager", "notes", "is_active"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class DepartmentForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "focal_person", "contact_number", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}
class VolunteerForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Volunteer
        fields = ["event", "full_name", "purok", "contact_number", "role", "status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}
class FeedbackForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["event", "respondent_name", "rating", "comments"]
        widgets = {"comments": forms.Textarea(attrs={"rows": 4})}