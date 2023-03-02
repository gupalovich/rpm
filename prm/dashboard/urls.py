from django.urls import path
from django.views.generic import TemplateView

from .apps import DashboardConfig
from .views import DashboardView

app_name = DashboardConfig.verbose_name

urlpatterns = [
    # path("~redirect/", view=DashboardRedirectView.as_view(), name="redirect"),
    # path("~settings/", DashboardSettingsView.as_view(), name="settings"),
    # path(
    #     "~settings/avatar-update/",
    #     AvatarUpdateView.as_view(),
    #     name="settings_avatar_update",
    # ),
    path("<str:username>/", DashboardView.as_view(), name="index"),
    path(
        "<str:username>/token/",
        TemplateView.as_view(template_name="dashboard/token.html"),
        name="token",
    ),
    path(
        "<str:username>/team/",
        TemplateView.as_view(template_name="dashboard/team.html"),
        name="team",
    ),
    path(
        "<str:username>/profile/",
        TemplateView.as_view(template_name="dashboard/profile.html"),
        name="profile",
    ),
]
