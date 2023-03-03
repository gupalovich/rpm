# from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from prm.users.tests.factories import UserFactory


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.url = reverse("dashboard:index", kwargs={"username": self.user.username})

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")

    def test_get_anon(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# class DashboardSettingsViewTests(TestCase):
#     def setUp(self):
#         self.user = UserFactory()
#         self.url = reverse("dashboard:settings")

#     def test_get(self):
#         self.client.force_login(self.user)
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, "dashboard/settings.html")

#     def test_get_anon(self):
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 302)


# class AvatarUpdateViewTests(TestCase):
#     def setUp(self):
#         self.user = UserFactory()
#         self.url = reverse("dashboard:settings_avatar_update")

#     def test_get(self):
#         self.client.force_login(self.user)
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 405)

#     def test_post_avatar_form(self):
#         self.client.force_login(self.user)
#         # read mock image
#         avatar = "test_avatar.jpg"
#         image = SimpleUploadedFile(
#             name=avatar,
#             content=open(f"backend/dashboard/tests/assets/{avatar}", "rb").read(),
#             content_type="image/jpeg",
#         )
#         data = {"avatar": image}
#         response = self.client.post(self.url, data)
#         self.user.refresh_from_db()
#         # tests
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json(), {"avatar_url": f"/media/avatars/{avatar}"})
#         self.assertEqual(self.user.avatar, f"avatars/{avatar}")

#     def test_post_avatar_form_invalid(self):
#         self.client.force_login(self.user)
#         # read mock image
#         data = {"avatar": ""}
#         response = self.client.post(self.url, data)
#         response_json = response.json()
#         self.user.refresh_from_db()
#         # tests
#         self.assertEqual(response.status_code, 400)
#         self.assertTrue(isinstance(response_json["error"], list))
#         self.assertEqual(self.user.avatar, "avatars/default.png")

#     def test_post_avatar_form_anon(self):
#         data = {"avatar": ""}
#         response = self.client.post(self.url, data)
#         self.assertEqual(response.status_code, 302)
