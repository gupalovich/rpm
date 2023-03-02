from django.contrib.auth import get_user_model
from django.urls import resolve, reverse

User = get_user_model()
url_prefix = "/board"


def test_dashboard_index(user: User):
    rev = reverse("dashboard:index", kwargs={"username": user.username})
    res = resolve(f"{url_prefix}/{user.username}/").view_name
    assert rev == f"{url_prefix}/{user.username}/"
    assert res == "dashboard:index"


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


# def test_redirect():
#     assert reverse("dashboard:redirect") == "/board/~redirect/"
#     assert resolve("/board/~redirect/").view_name == "dashboard:redirect"
