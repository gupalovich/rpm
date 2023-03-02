from django.urls import path
from django.views.generic import TemplateView

from .apps import DashboardConfig

app_name = DashboardConfig.verbose_name

urlpatterns = [
    path("", TemplateView.as_view(template_name="dashboard/index.html"), name="index"),
    path(
        "profile/",
        TemplateView.as_view(template_name="dashboard/profile.html"),
        name="profile",
    ),
    path(
        "team/", TemplateView.as_view(template_name="dashboard/team.html"), name="team"
    ),
    path(
        "token/",
        TemplateView.as_view(template_name="dashboard/token.html"),
        name="token",
    ),
]
