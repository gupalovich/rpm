from django.urls import path

from .apps import DashboardConfig
from .views import (
    AvatarUpdateView,
    DashboardIndexView,
    DashboardProfileView,
    DashboardRedirectView,
    DashboardTeamView,
    DashboardTokenView,
    update_index,
)

app_name = DashboardConfig.label

urlpatterns = [
    path("", view=DashboardRedirectView.as_view(), name="home-redirect"),
    path("~redirect/", view=DashboardRedirectView.as_view(), name="redirect"),
    path("~avatar-update/", AvatarUpdateView.as_view(), name="avatar_update"),
    path("update-index/", update_index, name="update_index_content"),
    path("<str:username>/", DashboardIndexView.as_view(), name="index"),
    path("<str:username>/token/", DashboardTokenView.as_view(), name="token"),
    path("<str:username>/team/", DashboardTeamView.as_view(), name="team"),
    path("<str:username>/profile/", DashboardProfileView.as_view(), name="profile"),
]
