from django.urls import path

from .apps import DashboardConfig
from .views import (
    DashboardIndexView,
    DashboardProfileView,
    DashboardRedirectView,
    DashboardTeamView,
    DashboardTokenView,
)

app_name = DashboardConfig.verbose_name

urlpatterns = [
    path("", view=DashboardRedirectView.as_view(), name="home-redirect"),
    path("~redirect/", view=DashboardRedirectView.as_view(), name="redirect"),
    path("<str:username>/", DashboardIndexView.as_view(), name="index"),
    path("<str:username>/token/", DashboardTokenView.as_view(), name="token"),
    path("<str:username>/team/", DashboardTeamView.as_view(), name="team"),
    path("<str:username>/profile/", DashboardProfileView.as_view(), name="profile"),
    # path(
    #     "<str:username>/profile/avatar-update/",
    #     AvatarUpdateView.as_view(),
    #     name="avatar_update",
    # ),
]
