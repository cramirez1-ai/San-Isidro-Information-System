from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView
from django.views import View


from .forms import (
    AnnouncementForm,
    BarangayProfileForm,
    BarangayOfficialForm,
    BlotterIncidentForm,
    CertificateForm,
    EventAttendeeForm,
    EventForm,
    EventResourceForm,
    HealthRecordForm,
    HouseholdForm,
    ProjectForm,
    ResidentForm,
    ResidentNotificationForm,
    ServiceForm,
    ServiceRequestForm,
)
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


BARANGAY_PROFILE = {
    "name": "Barangay San Isidro",
    "city": "Surigao City",
    "province": "Surigao del Norte",
    "region": "Caraga",
    "classification": "Rural barangay",
    "psgc_code": "1606724039",
    "correspondence_code": "166724039",
    "population_2020": "629",
    "city_population_2020": "171,107",
    "postal_code": "8400",
    "coordinates": "9.7536, 125.5707",
}


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


def apply_search(queryset, query, fields):
    if not query:
        return queryset
    condition = Q()
    for field in fields:
        condition |= Q(**{f"{field}__icontains": query})
    return queryset.filter(condition)


class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = "barangay/dashboard.html"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = BARANGAY_PROFILE
        context["stats"] = {
            "residents": Resident.objects.count(),
            "households": Household.objects.count(),
            "upcoming_events": Event.objects.exclude(
                status__in=[Event.Status.COMPLETED, Event.Status.CANCELLED]
            ).count(),
            "pending_requests": ServiceRequest.objects.filter(
                status__in=[ServiceRequest.Status.PENDING, ServiceRequest.Status.PROCESSING]
            ).count(),
            "open_blotters": BlotterIncident.objects.exclude(
                status__in=[BlotterIncident.Status.SETTLED, BlotterIncident.Status.CLOSED]
            ).count(),
        }
        context["announcements"] = Announcement.objects.filter(is_published=True)[:4]
        context["requests"] = ServiceRequest.objects.select_related("service", "resident")[:5]
        context["events"] = Event.objects.select_related("lead_official").exclude(
            status=Event.Status.CANCELLED
        )[:4]
        context["officials"] = BarangayOfficial.objects.filter(is_active=True)[:6]
        context["services"] = Service.objects.filter(is_active=True)[:6]
        return context


class SavedMessageMixin(AdminRequiredMixin):
    success_url = reverse_lazy("barangay:dashboard")
    success_message = "Record saved."

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.objects.create(
            user=self.request.user.username,
            module=self.model._meta.verbose_name.title() if self.model else "Record",
            action="Saved record",
            details=str(self.object),
        )
        messages.success(self.request, self.success_message)
        return response


class HouseholdListView(AdminRequiredMixin, ListView):
    model = Household
    template_name = "barangay/household_list.html"
    context_object_name = "households"
    paginate_by = 20

    def get_queryset(self):
        queryset = Household.objects.prefetch_related("residents")
        return apply_search(
            queryset,
            self.request.GET.get("q", "").strip(),
            ["household_number", "purok", "street_address", "contact_number"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["total_households"] = Household.objects.count()
        context["listed_households"] = (
            context["paginator"].count
            if context.get("paginator")
            else len(context["households"])
        )
        context["total_members"] = Resident.objects.filter(household__isnull=False).count()
        context["active_puroks"] = (
            Household.objects.exclude(purok="").values("purok").distinct().count()
        )
        context["assigned_heads"] = (
            Resident.objects.filter(household__isnull=False, is_household_head=True)
            .values("household")
            .distinct()
            .count()
        )
        return context


class HouseholdCreateView(SavedMessageMixin, CreateView):
    model = Household
    form_class = HouseholdForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:household_list")
    success_message = "Household record saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Household"
        context["back_url"] = reverse_lazy("barangay:household_list")
        return context


class HouseholdUpdateView(HouseholdCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Household"
        return context


class ResidentListView(AdminRequiredMixin, ListView):
    model = Resident
    template_name = "barangay/resident_list.html"
    context_object_name = "residents"
    paginate_by = 20

    def get_queryset(self):
        queryset = Resident.objects.select_related("household")
        queryset = apply_search(
            queryset,
            self.request.GET.get("q", "").strip(),
            ["first_name", "middle_name", "last_name", "contact_number", "occupation"],
        )
        gender = self.request.GET.get("gender")
        voter_status = self.request.GET.get("voter_status")
        if gender:
            queryset = queryset.filter(gender=gender)
        if voter_status:
            queryset = queryset.filter(voter_status=voter_status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["gender"] = self.request.GET.get("gender", "")
        context["voter_status"] = self.request.GET.get("voter_status", "")
        context["gender_choices"] = Resident.Gender.choices
        context["voter_choices"] = Resident.VoterStatus.choices
        return context


class ResidentDetailView(AdminRequiredMixin, DetailView):
    model = Resident
    template_name = "barangay/resident_detail.html"
    context_object_name = "resident"


class ResidentCreateView(SavedMessageMixin, CreateView):
    model = Resident
    form_class = ResidentForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:resident_list")
    success_message = "Resident record saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Resident"
        context["back_url"] = reverse_lazy("barangay:resident_list")
        return context


class ResidentUpdateView(ResidentCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Resident"
        return context


class OfficialListView(AdminRequiredMixin, ListView):
    model = BarangayOfficial
    template_name = "barangay/official_list.html"
    context_object_name = "officials"


class OfficialCreateView(SavedMessageMixin, CreateView):
    model = BarangayOfficial
    form_class = BarangayOfficialForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:official_list")
    success_message = "Official record saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Official"
        context["back_url"] = reverse_lazy("barangay:official_list")
        return context


class OfficialUpdateView(OfficialCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Official"
        return context


class ServiceListView(AdminRequiredMixin, ListView):
    model = Service
    template_name = "barangay/service_list.html"
    context_object_name = "services"


class ServiceCreateView(SavedMessageMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:service_list")
    success_message = "Service saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Service"
        context["back_url"] = reverse_lazy("barangay:service_list")
        return context


class ServiceUpdateView(ServiceCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Service"
        return context


class RequestListView(AdminRequiredMixin, ListView):
    model = ServiceRequest
    template_name = "barangay/request_list.html"
    context_object_name = "requests"
    paginate_by = 20

    def get_queryset(self):
        queryset = ServiceRequest.objects.select_related("service", "resident")
        queryset = apply_search(
            queryset,
            self.request.GET.get("q", "").strip(),
            ["request_number", "applicant_name", "resident__first_name", "resident__last_name", "purpose"],
        )
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["status"] = self.request.GET.get("status", "")
        context["status_choices"] = ServiceRequest.Status.choices
        return context


class RequestCreateView(SavedMessageMixin, CreateView):
    model = ServiceRequest
    form_class = ServiceRequestForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:request_list")
    success_message = "Service request saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Request"
        context["back_url"] = reverse_lazy("barangay:request_list")
        return context


class RequestUpdateView(RequestCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Request"
        return context


class CertificateListView(AdminRequiredMixin, ListView):
    model = Certificate
    template_name = "barangay/certificate_list.html"
    context_object_name = "certificates"
    paginate_by = 20

    def get_queryset(self):
        queryset = Certificate.objects.select_related("resident")
        queryset = apply_search(
            queryset,
            self.request.GET.get("q", "").strip(),
            [
                "certificate_number",
                "certificate_type",
                "applicant_name",
                "resident__first_name",
                "resident__last_name",
                "purpose",
            ],
        )
        status = self.request.GET.get("status")
        certificate_type = self.request.GET.get("certificate_type")
        if status:
            queryset = queryset.filter(status=status)
        if certificate_type:
            queryset = queryset.filter(certificate_type=certificate_type)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["status"] = self.request.GET.get("status", "")
        context["certificate_type"] = self.request.GET.get("certificate_type", "")
        context["status_choices"] = Certificate.Status.choices
        context["type_choices"] = Certificate.CertificateType.choices
        context["issued_count"] = Certificate.objects.filter(status=Certificate.Status.ISSUED).count()
        context["claimed_count"] = Certificate.objects.filter(status=Certificate.Status.CLAIMED).count()
        return context


class CertificateCreateView(SavedMessageMixin, CreateView):
    model = Certificate
    form_class = CertificateForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:certificate_list")
    success_message = "Certificate record saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Certificate"
        context["back_url"] = reverse_lazy("barangay:certificate_list")
        return context


class CertificateUpdateView(CertificateCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Certificate"
        return context


class AnnouncementListView(AdminRequiredMixin, ListView):
    model = Announcement
    template_name = "barangay/announcement_list.html"
    context_object_name = "announcements"


class AnnouncementCreateView(SavedMessageMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:announcement_list")
    success_message = "Announcement saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Announcement"
        context["back_url"] = reverse_lazy("barangay:announcement_list")
        return context


class AnnouncementUpdateView(AnnouncementCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Announcement"
        return context


class EventListView(AdminRequiredMixin, ListView):
    model = Event
    template_name = "barangay/event_list.html"
    context_object_name = "events"
    paginate_by = 20

    def get_queryset(self):
        queryset = Event.objects.select_related("lead_official").prefetch_related("attendees", "resources")
        queryset = apply_search(
            queryset,
            self.request.GET.get("q", "").strip(),
            ["title", "venue", "organizer", "target_audience", "description"],
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
        upcoming = Event.objects.exclude(status__in=[Event.Status.COMPLETED, Event.Status.CANCELLED])
        context["query"] = self.request.GET.get("q", "")
        context["status"] = self.request.GET.get("status", "")
        context["category"] = self.request.GET.get("category", "")
        context["status_choices"] = Event.Status.choices
        context["category_choices"] = Event.Category.choices
        context["total_events"] = Event.objects.count()
        context["upcoming_events"] = upcoming.count()
        context["public_events"] = Event.objects.filter(is_public=True).count()
        context["registered_attendees"] = EventAttendee.objects.count()
        return context


class EventDetailView(AdminRequiredMixin, DetailView):
    model = Event
    template_name = "barangay/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.select_related("lead_official").prefetch_related("attendees__resident", "resources")


class EventCreateView(SavedMessageMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:event_list")
    success_message = "Event saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Event"
        context["back_url"] = reverse_lazy("barangay:event_list")
        return context


class EventUpdateView(EventCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Event"
        return context


class EventAttendeeCreateView(SavedMessageMixin, CreateView):
    model = EventAttendee
    form_class = EventAttendeeForm
    template_name = "barangay/form.html"
    success_message = "Event attendee saved."

    def get_initial(self):
        initial = super().get_initial()
        event_id = self.kwargs.get("event_pk")
        if event_id:
            initial["event"] = event_id
        return initial

    def get_success_url(self):
        return reverse_lazy("barangay:event_detail", args=[self.object.event_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_id = self.kwargs.get("event_pk")
        context["title"] = "Add Event Attendee"
        context["back_url"] = (
            reverse_lazy("barangay:event_detail", args=[event_id])
            if event_id
            else reverse_lazy("barangay:event_list")
        )
        return context


class EventResourceCreateView(SavedMessageMixin, CreateView):
    model = EventResource
    form_class = EventResourceForm
    template_name = "barangay/form.html"
    success_message = "Event resource saved."

    def get_initial(self):
        initial = super().get_initial()
        event_id = self.kwargs.get("event_pk")
        if event_id:
            initial["event"] = event_id
        return initial

    def get_success_url(self):
        return reverse_lazy("barangay:event_detail", args=[self.object.event_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_id = self.kwargs.get("event_pk")
        context["title"] = "Add Event Resource"
        context["back_url"] = (
            reverse_lazy("barangay:event_detail", args=[event_id])
            if event_id
            else reverse_lazy("barangay:event_list")
        )
        return context


class BlotterListView(AdminRequiredMixin, ListView):
    model = BlotterIncident
    template_name = "barangay/blotter_list.html"
    context_object_name = "incidents"
    paginate_by = 20

    def get_queryset(self):
        queryset = BlotterIncident.objects.all()
        queryset = apply_search(
            queryset,
            self.request.GET.get("q", "").strip(),
            ["case_number", "complainant_name", "respondent_name", "incident_type", "location"],
        )
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_incidents = BlotterIncident.objects.count()
        active_incidents = BlotterIncident.objects.exclude(
            status__in=[BlotterIncident.Status.SETTLED, BlotterIncident.Status.CLOSED]
        ).count()
        status_counts = dict(
            BlotterIncident.objects.values_list("status").annotate(total=Count("id"))
        )
        context["query"] = self.request.GET.get("q", "")
        context["status"] = self.request.GET.get("status", "")
        context["status_choices"] = BlotterIncident.Status.choices
        context["listed_incidents"] = (
            context["paginator"].count
            if context.get("paginator")
            else len(context["incidents"])
        )
        context["total_incidents"] = total_incidents
        context["active_incidents"] = active_incidents
        context["mediation_incidents"] = status_counts.get(BlotterIncident.Status.MEDIATION, 0)
        context["settled_incidents"] = status_counts.get(BlotterIncident.Status.SETTLED, 0)
        return context


class BlotterCreateView(SavedMessageMixin, CreateView):
    model = BlotterIncident
    form_class = BlotterIncidentForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:blotter_list")
    success_message = "Blotter incident saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Blotter Incident"
        context["back_url"] = reverse_lazy("barangay:blotter_list")
        return context


class BlotterUpdateView(BlotterCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Blotter Incident"
        return context


class ReportsView(AdminRequiredMixin, TemplateView):
    template_name = "barangay/reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = {
            "residents": Resident.objects.count(),
            "households": Household.objects.count(),
            "certificates": Certificate.objects.count(),
            "issued_certificates": Certificate.objects.filter(status=Certificate.Status.ISSUED).count(),
            "blotters": BlotterIncident.objects.count(),
            "open_blotters": BlotterIncident.objects.exclude(
                status__in=[BlotterIncident.Status.SETTLED, BlotterIncident.Status.CLOSED]
            ).count(),
            "requests": ServiceRequest.objects.count(),
            "projects": Project.objects.count(),
        }
        context["certificate_types"] = Certificate.objects.values("certificate_type").annotate(total=Count("id"))
        context["blotter_statuses"] = BlotterIncident.objects.values("status").annotate(total=Count("id"))
        context["recent_certificates"] = Certificate.objects.select_related("resident")[:8]
        context["recent_blotters"] = BlotterIncident.objects.all()[:8]
        return context


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "barangay/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return User.objects.order_by("-is_superuser", "-is_staff", "username")


class SettingsView(AdminRequiredMixin, UpdateView):
    model = BarangayProfile
    form_class = BarangayProfileForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:settings")
    success_message = "Barangay settings saved."

    def get_object(self, queryset=None):
        return BarangayProfile.current()

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.objects.create(
            user=self.request.user.username,
            module="Settings",
            action="Updated barangay profile",
            details=str(self.object),
        )
        messages.success(self.request, self.success_message)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Barangay Settings"
        context["back_url"] = reverse_lazy("barangay:dashboard")
        return context


class HealthRecordListView(AdminRequiredMixin, ListView):
    model = HealthRecord
    template_name = "barangay/health_record_list.html"
    context_object_name = "records"
    paginate_by = 20

    def get_queryset(self):
        queryset = HealthRecord.objects.select_related("resident")
        queryset = apply_search(
            queryset,
            self.request.GET.get("q", "").strip(),
            ["name", "resident__first_name", "resident__last_name", "details"],
        )
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["category"] = self.request.GET.get("category", "")
        context["category_choices"] = HealthRecord.Category.choices
        return context


class HealthRecordCreateView(SavedMessageMixin, CreateView):
    model = HealthRecord
    form_class = HealthRecordForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:health_list")
    success_message = "Health record saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Health Record"
        context["back_url"] = reverse_lazy("barangay:health_list")
        return context


class HealthRecordUpdateView(HealthRecordCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Health Record"
        return context


class ProjectListView(AdminRequiredMixin, ListView):
    model = Project
    template_name = "barangay/project_list.html"
    context_object_name = "projects"
    paginate_by = 20

    def get_queryset(self):
        queryset = Project.objects.select_related("lead_official")
        queryset = apply_search(
            queryset,
            self.request.GET.get("q", "").strip(),
            ["title", "description", "funding_source"],
        )
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["status"] = self.request.GET.get("status", "")
        context["status_choices"] = Project.Status.choices
        return context


class ProjectCreateView(SavedMessageMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:project_list")
    success_message = "Project saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Project"
        context["back_url"] = reverse_lazy("barangay:project_list")
        return context


class ProjectUpdateView(ProjectCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Project"
        return context


class NotificationListView(AdminRequiredMixin, ListView):
    model = ResidentNotification
    template_name = "barangay/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20


class NotificationCreateView(SavedMessageMixin, CreateView):
    model = ResidentNotification
    form_class = ResidentNotificationForm
    template_name = "barangay/form.html"
    success_url = reverse_lazy("barangay:notification_list")
    success_message = "Notification saved."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Notification"
        context["back_url"] = reverse_lazy("barangay:notification_list")
        return context


class NotificationUpdateView(NotificationCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Notification"
        return context


class AuditLogListView(AdminRequiredMixin, ListView):
    model = AuditLog
    template_name = "barangay/audit_log_list.html"
    context_object_name = "logs"
    paginate_by = 30
class ResidentPDFView(AdminRequiredMixin, View):
    def get(self, request):
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="residents.pdf"'
        p = canvas.Canvas(response, pagesize=letter)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(150, 750, "Barangay San Isidro - Resident List")
        p.setFont("Helvetica", 11)
        y = 710
        for r in Resident.objects.all():
            p.drawString(50, y, f"{r.last_name}, {r.first_name} | {r.gender} | {r.civil_status} | Age: {r.age}")
            y -= 22
            if y < 60:
                p.showPage()
                y = 750
        p.save()
        return response