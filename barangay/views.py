from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from .forms import (
    AnnouncementForm,
    BarangayOfficialForm,
    BlotterIncidentForm,
    HouseholdForm,
    ResidentForm,
    ServiceForm,
    ServiceRequestForm,
    UserRegistrationForm,
)
from .models import (
    Announcement,
    BarangayOfficial,
    BlotterIncident,
    Household,
    Resident,
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


def apply_search(queryset, query, fields):
    if not query:
        return queryset
    condition = Q()
    for field in fields:
        condition |= Q(**{f"{field}__icontains": query})
    return queryset.filter(condition)


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("barangay:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Account created. Welcome to the system.")
        return response


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "barangay/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = BARANGAY_PROFILE
        context["stats"] = {
            "residents": Resident.objects.count(),
            "households": Household.objects.count(),
            "pending_requests": ServiceRequest.objects.filter(
                status__in=[ServiceRequest.Status.PENDING, ServiceRequest.Status.PROCESSING]
            ).count(),
            "open_blotters": BlotterIncident.objects.exclude(
                status__in=[BlotterIncident.Status.SETTLED, BlotterIncident.Status.CLOSED]
            ).count(),
        }
        context["announcements"] = Announcement.objects.filter(is_published=True)[:4]
        context["requests"] = ServiceRequest.objects.select_related("service", "resident")[:5]
        context["officials"] = BarangayOfficial.objects.filter(is_active=True)[:6]
        context["services"] = Service.objects.filter(is_active=True)[:6]
        return context


class SavedMessageMixin(LoginRequiredMixin):
    success_url = reverse_lazy("barangay:dashboard")
    success_message = "Record saved."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class HouseholdListView(LoginRequiredMixin, ListView):
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


class ResidentListView(LoginRequiredMixin, ListView):
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


class ResidentDetailView(LoginRequiredMixin, DetailView):
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


class OfficialListView(LoginRequiredMixin, ListView):
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


class ServiceListView(LoginRequiredMixin, ListView):
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


class RequestListView(LoginRequiredMixin, ListView):
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


class AnnouncementListView(LoginRequiredMixin, ListView):
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


class BlotterListView(LoginRequiredMixin, ListView):
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

# Create your views here.
