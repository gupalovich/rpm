from django.urls import path

from .apps import DashboardConfig
from .views import (
    AvatarUpdateView,
    DashboardIndexView,
    DashboardProfileView,
    DashboardRedirectView,
    DashboardTeamView,
    DashboardTokenView,
    PollTokenActiveRound,
    PollTokenRounds,
    PollUserBalance,
    PollUserTransactions,
)

app_name = DashboardConfig.label

urlpatterns = [
    path("", view=DashboardRedirectView.as_view(), name="home_redirect"),
    path("~redirect/", view=DashboardRedirectView.as_view(), name="redirect"),
    path("~avatar-update/", AvatarUpdateView.as_view(), name="avatar_update"),
    # Polling views
    path("~poll-user-balance/", PollUserBalance.as_view(), name="poll_user_balance"),
    path(
        "~poll-active-round/", PollTokenActiveRound.as_view(), name="poll_active_round"
    ),
    path("~poll-token-rounds/", PollTokenRounds.as_view(), name="poll_token_rounds"),
    path(
        "~poll-user-transactions/",
        PollUserTransactions.as_view(),
        name="poll_user_transactions",
    ),
    # Generic views
    path("<str:username>/", DashboardIndexView.as_view(), name="index"),
    path("<str:username>/token/", DashboardTokenView.as_view(), name="token"),
    path("<str:username>/team/", DashboardTeamView.as_view(), name="team"),
    path("<str:username>/profile/", DashboardProfileView.as_view(), name="profile"),
]
