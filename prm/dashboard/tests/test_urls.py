from django.contrib.auth import get_user_model
from django.urls import resolve, reverse

User = get_user_model()


def test_dashboard_redirect():
    assert reverse("dashboard:redirect") == "/dashboard/~redirect/"
    assert resolve("/dashboard/~redirect/").view_name == "dashboard:redirect"


def test_dashboard_avatar_update():
    assert reverse("dashboard:avatar_update") == "/dashboard/~avatar-update/"
    assert resolve("/dashboard/~avatar-update/").view_name == "dashboard:avatar_update"


def test_dashboard_index(user: User):
    rev = reverse("dashboard:index", kwargs={"username": user.username})
    res = resolve(f"/dashboard/{user.username}/").view_name
    assert rev == f"/dashboard/{user.username}/"
    assert res == "dashboard:index"


def test_dashboard_token(user: User):
    rev = reverse("dashboard:token", kwargs={"username": user.username})
    res = resolve(f"/dashboard/{user.username}/token/").view_name
    assert rev == f"/dashboard/{user.username}/token/"
    assert res == "dashboard:token"


def test_dashboard_team(user: User):
    rev = reverse("dashboard:team", kwargs={"username": user.username})
    res = resolve(f"/dashboard/{user.username}/team/").view_name
    assert rev == f"/dashboard/{user.username}/team/"
    assert res == "dashboard:team"


def test_dashboard_profile(user: User):
    rev = reverse("dashboard:profile", kwargs={"username": user.username})
    res = resolve(f"/dashboard/{user.username}/profile/").view_name
    assert rev == f"/dashboard/{user.username}/profile/"
    assert res == "dashboard:profile"
