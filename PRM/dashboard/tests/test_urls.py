from django.contrib.auth import get_user_model
from django.urls import resolve, reverse

User = get_user_model()


def test_dashboard_index(user: User):
    rev = reverse("dashboard:index", kwargs={"username": user.username})
    res = resolve(f"/dashboard/{user.username}/").view_name
    assert rev == f"/dashboard/{user.username}/"
    assert res == "dashboard:index"


def test_redirect():
    assert reverse("dashboard:redirect") == "/dashboard/~redirect/"
    assert resolve("/dashboard/~redirect/").view_name == "dashboard:redirect"


# def test_dashboard_settings():
#     rev = reverse("dashboard:settings")
#     res = resolve(f"{url_prefix}/~settings/").view_name
#     assert rev == f"{url_prefix}/~settings/"
#     assert res == "dashboard:settings"


# def test_dashboard_settings_avatar_update():
#     rev = reverse("dashboard:settings_avatar_update")
#     res = resolve(f"{url_prefix}/~settings/avatar-update/").view_name
#     assert rev == f"{url_prefix}/~settings/avatar-update/"
#     assert res == "dashboard:settings_avatar_update"
