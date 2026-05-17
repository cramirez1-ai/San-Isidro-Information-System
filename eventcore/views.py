from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models.deletion import ProtectedError
from django.db.models import Count, Q, Sum
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Announcement, Attendee, BudgetItem, Department, Event, Feedback, Resource, Venue, Volunteer
import json
import csv
import calendar

from .forms import (
    AnnouncementForm,
    AttendeeForm,
    BudgetItemForm,
    DepartmentForm,
    EventForm,
    RegisterForm,
    ResourceForm,
   VenueForm,
    VolunteerForm,
    FeedbackForm,
)


BARANGAY_PROFILE = {
    "name": "Barangay San Isidro",
    "city": "Surigao City",
    "province": "Surigao del Norte",
    "region": "Caraga",
    "tagline": "EventCore command center for public programs, logistics, and community coordination.",
}


def search(queryset, query, fields):
    if not query:
        return queryset
    condition = Q()
    for field in fields:
        condition |= Q(**{f"{field}__icontains": query})
    return queryset.filter(condition)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("eventcore:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Account created. Welcome to EventCore.")
        return response


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "eventcore/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_statuses = [Event.Status.PLANNING, Event.Status.SCHEDULED, Event.Status.ONGOING]
        context["profile"] = BARANGAY_PROFILE
        total_events = Event.objects.count()
        active_events = Event.objects.filter(status__in=active_statuses).count()
        completion_rate = round((active_events / total_events) * 100) if total_events else 0

        context["stats"] = {
            "events": total_events,
            "active_events": active_events,
            "attendees": Attendee.objects.count(),
            "resources_ready": Resource.objects.filter(status__in=[Resource.Status.READY, Resource.Status.RETURNED]).count(),
            "budget": BudgetItem.objects.aggregate(total=Sum("amount"))["total"] or 0,
            "completion_rate": completion_rate,
        }
        context["events"] = Event.objects.select_related("venue", "department").exclude(status=Event.Status.CANCELLED)[:5]
        context["announcements"] = Announcement.objects.filter(is_published=True)[:4]
        context["category_counts"] = Event.objects.values("category").annotate(total=Count("id")).order_by("category")
        return context


class SavedMixin(LoginRequiredMixin):
    success_message = "Record saved."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class DeleteMessageMixin(LoginRequiredMixin, DeleteView):
    template_name = "eventcore/confirm_delete.html"
    success_message = "Record deleted."
    protected_message = "This record cannot be deleted because it is being used by other records."

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, self.protected_message)
            return redirect(success_url)
        messages.success(self.request, self.success_message)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("title", f"Delete {self.object}")
        context.setdefault("back_url", self.get_success_url())
        return context


class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = "eventcore/event_list.html"
    context_object_name = "events"
    paginate_by = 12

    def get_queryset(self):
        queryset = Event.objects.select_related("venue", "department").prefetch_related("attendees", "resources")
        queryset = search(
            queryset,
            self.request.GET.get("q", "").strip(),
            ["title", "description", "venue__name", "organizer", "target_audience"],
        )
        status = self.request.GET.get("status")
        category = self.request.GET.get("category")
        if status:
            queryset = queryset.filter(status=status)
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["status"] = self.request.GET.get("status", "")
        context["category"] = self.request.GET.get("category", "")
        context["status_choices"] = Event.Status.choices
        context["category_choices"] = Event.Category.choices
        context["total_events"] = Event.objects.count()
        context["public_events"] = Event.objects.filter(is_public=True).count()
        context["active_events"] = Event.objects.exclude(status__in=[Event.Status.COMPLETED, Event.Status.CANCELLED]).count()
        context["attendee_total"] = Attendee.objects.count()
        return context


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = "eventcore/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.select_related("venue", "department").prefetch_related("attendees", "resources", "budget_items", "announcements")


class EventCreateView(SavedMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "eventcore/form.html"
    success_message = "Event saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Event"
        context["back_url"] = reverse_lazy("eventcore:event_list")
        return context


class EventUpdateView(EventCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Event"
        return context


class EventDeleteView(DeleteMessageMixin):
    model = Event
    success_url = reverse_lazy("eventcore:event_list")
    success_message = "Event deleted."


class ChildCreateMixin(SavedMixin, CreateView):
    template_name = "eventcore/form.html"
    event_field_name = "event"

    def get_initial(self):
        initial = super().get_initial()
        event_pk = self.kwargs.get("event_pk")
        if event_pk:
            initial[self.event_field_name] = event_pk
        return initial

    def get_success_url(self):
        return reverse_lazy("eventcore:event_detail", args=[self.object.event_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_pk = self.kwargs.get("event_pk")
        context["back_url"] = reverse_lazy("eventcore:event_detail", args=[event_pk])
        return context


class AttendeeCreateView(ChildCreateMixin):
    model = Attendee
    form_class = AttendeeForm
    success_message = "Attendee saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Attendee"
        return context


class AttendeeUpdateView(SavedMixin, UpdateView):
    model = Attendee
    form_class = AttendeeForm
    template_name = "eventcore/form.html"
    success_message = "Attendee updated."

    def get_success_url(self):
        return reverse("eventcore:event_detail", args=[self.object.event_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Attendee"
        context["back_url"] = self.get_success_url()
        return context


class AttendeeDeleteView(DeleteMessageMixin):
    model = Attendee
    success_message = "Attendee deleted."

    def get_success_url(self):
        return reverse("eventcore:event_detail", args=[self.object.event_id])


class ResourceCreateView(ChildCreateMixin):
    model = Resource
    form_class = ResourceForm
    success_message = "Resource saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Resource"
        return context


class ResourceUpdateView(SavedMixin, UpdateView):
    model = Resource
    form_class = ResourceForm
    template_name = "eventcore/form.html"
    success_message = "Resource updated."

    def get_success_url(self):
        return reverse("eventcore:event_detail", args=[self.object.event_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Resource"
        context["back_url"] = self.get_success_url()
        return context


class ResourceDeleteView(DeleteMessageMixin):
    model = Resource
    success_message = "Resource deleted."

    def get_success_url(self):
        return reverse("eventcore:event_detail", args=[self.object.event_id])


class BudgetItemCreateView(ChildCreateMixin):
    model = BudgetItem
    form_class = BudgetItemForm
    success_message = "Budget item saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Budget Item"
        return context


class BudgetItemUpdateView(SavedMixin, UpdateView):
    model = BudgetItem
    form_class = BudgetItemForm
    template_name = "eventcore/form.html"
    success_message = "Budget item updated."

    def get_success_url(self):
        return reverse("eventcore:event_detail", args=[self.object.event_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Budget Item"
        context["back_url"] = self.get_success_url()
        return context


class BudgetItemDeleteView(DeleteMessageMixin):
    model = BudgetItem
    success_message = "Budget item deleted."

    def get_success_url(self):
        return reverse("eventcore:event_detail", args=[self.object.event_id])


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = "eventcore/announcement_list.html"
    context_object_name = "announcements"


class AnnouncementCreateView(SavedMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "eventcore/form.html"
    success_url = reverse_lazy("eventcore:announcement_list")
    success_message = "Announcement saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Announcement"
        context["back_url"] = reverse_lazy("eventcore:announcement_list")
        return context


class AnnouncementUpdateView(AnnouncementCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Announcement"
        return context


class AnnouncementDeleteView(DeleteMessageMixin):
    model = Announcement
    success_url = reverse_lazy("eventcore:announcement_list")
    success_message = "Announcement deleted."


class VenueListView(LoginRequiredMixin, ListView):
    model = Venue
    template_name = "eventcore/venue_list.html"
    context_object_name = "venues"


class VenueCreateView(SavedMixin, CreateView):
    model = Venue
    form_class = VenueForm
    template_name = "eventcore/form.html"
    success_url = reverse_lazy("eventcore:venue_list")
    success_message = "Venue saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Venue"
        context["back_url"] = reverse_lazy("eventcore:venue_list")
        return context


class VenueUpdateView(VenueCreateView, UpdateView):
    success_message = "Venue updated."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Venue"
        return context


class VenueDeleteView(DeleteMessageMixin):
    model = Venue
    success_url = reverse_lazy("eventcore:venue_list")
    success_message = "Venue deleted."
    protected_message = "This venue cannot be deleted while events are assigned to it."


class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = "eventcore/department_list.html"
    context_object_name = "departments"


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = "eventcore/form.html"
    success_url = reverse_lazy("eventcore:department_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Department"
        context["submit_text"] = "Create Department"
        context["back_url"] = reverse_lazy("eventcore:department_list")
        return context


class DepartmentUpdateView(SavedMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = "eventcore/form.html"
    success_url = reverse_lazy("eventcore:department_list")
    success_message = "Department updated."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Department"
        context["back_url"] = reverse_lazy("eventcore:department_list")
        return context


class DepartmentDeleteView(DeleteMessageMixin):
    model = Department
    success_url = reverse_lazy("eventcore:department_list")
    success_message = "Department deleted."


class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = "eventcore/calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        year = int(self.request.GET.get('year', today.year))
        month = int(self.request.GET.get('month', today.month))

        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        events = Event.objects.filter(
            start_at__date__gte=start_date,
            start_at__date__lt=end_date
        ).select_related('venue')

        cal = calendar.Calendar(firstweekday=calendar.SUNDAY).monthdayscalendar(year, month)

        calendar_days = []
        for week in cal:
            for day in week:
                if day == 0:
                    calendar_days.append({'day': '', 'date': None, 'events': []})
                else:
                    day_date = datetime(year, month, day).date()
                    day_events = [event for event in events if timezone.localtime(event.start_at).date() == day_date]
                    calendar_days.append({
                        'day': day,
                        'date': day_date,
                        'events': day_events
                    })

        context.update({
            'year': year,
            'month': month,
            'month_label': start_date.strftime("%B %Y"),
            'events': events,
            'today': today,
            'calendar_days': calendar_days,
        })
        return context


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "eventcore/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()

        if query:
            events = Event.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(organizer__icontains=query) |
                Q(target_audience__icontains=query) |
                Q(venue__name__icontains=query)
            ).select_related('venue', 'department')[:10]

            announcements = Announcement.objects.filter(
                Q(title__icontains=query) |
                Q(body__icontains=query)
            ).select_related('event')[:10]

            attendees = Attendee.objects.filter(
                Q(full_name__icontains=query) |
                Q(purok__icontains=query) |
                Q(contact_number__icontains=query)
            ).select_related('event')[:10]

            context.update({
                'query': query,
                'events': events,
                'announcements': announcements,
                'attendees': attendees,
            })

        return context


def export_events_csv(request):
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="events_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Category', 'Venue', 'Start Date', 'End Date', 'Status', 'Expected Attendees'])

    events = Event.objects.select_related('venue').all()
    for event in events:
        writer.writerow([
            event.title,
            event.category,
            event.venue.name if event.venue else '',
            event.start_at.strftime('%Y-%m-%d %H:%M'),
            event.end_at.strftime('%Y-%m-%d %H:%M'),
            event.status,
            event.expected_attendees,
        ])

    return response


def api_events_json(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    events = Event.objects.select_related('venue').all()
    events_data = []

    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'category': event.category,
            'venue': event.venue.name if event.venue else '',
            'start': event.start_at.isoformat(),
            'end': event.end_at.isoformat(),
            'status': event.status,
            'attendees': event.expected_attendees,
        })

    return JsonResponse({'events': events_data})


@login_required
@require_POST
def approve_event(request, pk):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect("eventcore:event_detail", pk=pk)

    event = Event.objects.get(pk=pk)
    action = request.POST.get("action")
    notes = request.POST.get("approval_notes", "")

    if action == "approve":
        event.approval_status = Event.ApprovalStatus.APPROVED
        messages.success(request, f'"{event.title}" approved!')
    elif action == "reject":
        event.approval_status = Event.ApprovalStatus.REJECTED
        messages.warning(request, f'"{event.title}" rejected.')

    event.approval_notes = notes
    event.save()
    return redirect("eventcore:event_detail", pk=pk)
from django.contrib.auth.models import Group, Permission

def setup_roles(request):
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    staff_group, _ = Group.objects.get_or_create(name='Staff')

    # Admin → all permissions
    admin_group.permissions.set(Permission.objects.all())

    # Staff → limited permissions
    staff_permissions = Permission.objects.filter(codename__in=[
        'add_event',
        'change_event',
        'view_event',
        'add_attendee',
        'view_attendee',
    ])
    staff_group.permissions.set(staff_permissions)

    return HttpResponse("Roles created successfully!")
class ArchivedEventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = "eventcore/archived_events.html"
    context_object_name = "events"
    paginate_by = 12

    def get_queryset(self):
        return Event.objects.filter(
            status=Event.Status.COMPLETED
        ).select_related("venue", "department").order_by("-end_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_archived"] = Event.objects.filter(
            status=Event.Status.COMPLETED
        ).count()
        return context
class VolunteerListView(LoginRequiredMixin, ListView):
    model = Volunteer
    template_name = "eventcore/volunteer_list.html"
    context_object_name = "volunteers"
    paginate_by = 12

    def get_queryset(self):
        return Volunteer.objects.select_related("event").order_by("-id")


class VolunteerCreateView(ChildCreateMixin):
    model = Volunteer
    form_class = VolunteerForm
    success_message = "Volunteer saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Volunteer"
        return context


class VolunteerUpdateView(SavedMixin, UpdateView):
    model = Volunteer
    form_class = VolunteerForm
    template_name = "eventcore/form.html"
    success_message = "Volunteer updated."

    def get_success_url(self):
        return reverse("eventcore:event_detail", args=[self.object.event_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Volunteer"
        context["back_url"] = self.get_success_url()
        return context


class VolunteerDeleteView(DeleteMessageMixin):
    model = Volunteer
    success_message = "Volunteer deleted."

    def get_success_url(self):
        return reverse("eventcore:event_detail", args=[self.object.event_id])
class FeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = "eventcore/feedback_list.html"
    context_object_name = "feedbacks"
    paginate_by = 12

    def get_queryset(self):
        return Feedback.objects.select_related("event").order_by("-submitted_at")


class FeedbackCreateView(ChildCreateMixin):
    model = Feedback
    form_class = FeedbackForm
    success_message = "Feedback saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Feedback"
        return context


class FeedbackDeleteView(DeleteMessageMixin):
    model = Feedback
    success_message = "Feedback deleted."

    def get_success_url(self):
        return reverse("eventcore:event_detail", args=[self.object.event_id])
class ReportView(LoginRequiredMixin, TemplateView):
    template_name = "eventcore/report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_events"] = Event.objects.count()
        context["completed"] = Event.objects.filter(status=Event.Status.COMPLETED).count()
        context["total_attendees"] = Attendee.objects.count()
        context["total_volunteers"] = Volunteer.objects.count()
        context["total_budget"] = BudgetItem.objects.aggregate(total=Sum("amount"))["total"] or 0
        context["events"] = Event.objects.select_related("venue","department").annotate(
            attendee_count=Count("attendees"),
            budget_total=Sum("budget_items__amount")
        ).order_by("-start_at")
        context["category_counts"] = Event.objects.values("category").annotate(total=Count("id"))
        return context
class ParticipantView(LoginRequiredMixin, ListView):
    model = Attendee
    template_name = "eventcore/participant_list.html"
    context_object_name = "attendees"
    paginate_by = 15

    def get_queryset(self):
        return Attendee.objects.select_related("event").order_by("full_name")
    
def export_event_ical(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    event = Event.objects.select_related('venue').get(pk=pk)

    def ical_dt(dt):
        return dt.strftime('%Y%m%dT%H%M%S')

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Barangay EventCore//EN",
        "BEGIN:VEVENT",
        f"UID:{event.pk}@eventcore.barangay",
        f"DTSTART:{ical_dt(event.start_at)}",
        f"DTEND:{ical_dt(event.end_at)}",
        f"SUMMARY:{event.title}",
        f"DESCRIPTION:{event.description[:200] if event.description else ''}",
        f"LOCATION:{event.venue.name if event.venue else ''}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]

    content = "\r\n".join(lines)
    response = HttpResponse(content, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="event_{event.pk}.ics"'
    return response
