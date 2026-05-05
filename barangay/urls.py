from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "barangay"

urlpatterns = [
    path("accounts/register/", views.RegisterView.as_view(), name="register"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page=reverse_lazy("barangay:login")),
        name="logout",
    ),
    path(
        "accounts/password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url=reverse_lazy("barangay:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "accounts/password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("barangay:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("households/", views.HouseholdListView.as_view(), name="household_list"),
    path("households/add/", views.HouseholdCreateView.as_view(), name="household_add"),
    path("households/new/", views.HouseholdCreateView.as_view(), name="household_create"),
    path("households/<int:pk>/edit/", views.HouseholdUpdateView.as_view(), name="household_update"),
    path("residents/", views.ResidentListView.as_view(), name="resident_list"),
    path("residents/add/", views.ResidentCreateView.as_view(), name="resident_add"),
    path("residents/new/", views.ResidentCreateView.as_view(), name="resident_create"),
    path("residents/<int:pk>/", views.ResidentDetailView.as_view(), name="resident_detail"),
    path("residents/<int:pk>/edit/", views.ResidentUpdateView.as_view(), name="resident_update"),
    path("officials/", views.OfficialListView.as_view(), name="official_list"),
    path("officials/add/", views.OfficialCreateView.as_view(), name="official_add"),
    path("officials/new/", views.OfficialCreateView.as_view(), name="official_create"),
    path("officials/<int:pk>/edit/", views.OfficialUpdateView.as_view(), name="official_update"),
    path("services/", views.ServiceListView.as_view(), name="service_list"),
    path("services/add/", views.ServiceCreateView.as_view(), name="service_add"),
    path("services/new/", views.ServiceCreateView.as_view(), name="service_create"),
    path("services/<int:pk>/edit/", views.ServiceUpdateView.as_view(), name="service_update"),
    path("requests/", views.RequestListView.as_view(), name="request_list"),
    path("requests/add/", views.RequestCreateView.as_view(), name="request_add"),
    path("requests/new/", views.RequestCreateView.as_view(), name="request_create"),
    path("requests/<int:pk>/edit/", views.RequestUpdateView.as_view(), name="request_update"),
    path("announcements/", views.AnnouncementListView.as_view(), name="announcement_list"),
    path("announcements/add/", views.AnnouncementCreateView.as_view(), name="announcement_add"),
    path("announcements/new/", views.AnnouncementCreateView.as_view(), name="announcement_create"),
    path(
        "announcements/<int:pk>/edit/",
        views.AnnouncementUpdateView.as_view(),
        name="announcement_update",
    ),
    path("blotter/", views.BlotterListView.as_view(), name="blotter_list"),
    path("blotter/add/", views.BlotterCreateView.as_view(), name="blotter_add"),
    path("blotter/new/", views.BlotterCreateView.as_view(), name="blotter_create"),
    path("blotter/<int:pk>/edit/", views.BlotterUpdateView.as_view(), name="blotter_update"),
]
