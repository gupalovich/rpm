from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from prm.tokens.tests.factories import TokenFactory, TokenRound, TokenRoundFactory
from prm.users.tests.factories import UserFactory


class HomeRedirectViewTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.user.get_absolute_url())

    def test_get_anon(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("account_login"))


class DashboardRedirectViewTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.url = reverse("dashboard:redirect")
        self.url_home = reverse("dashboard:home-redirect")

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.user.get_absolute_url())

    def test_get_anon(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.url}")

    def test_get_home(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url_home)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.user.get_absolute_url())

    def test_get_home_anon(self):
        response = self.client.get(self.url_home)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"{reverse('account_login')}?next={self.url_home}"
        )


class DashboardIndexViewTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.url = reverse("dashboard:index", kwargs={"username": self.user.username})
        self.token_round = TokenRoundFactory()
        self.token_rounds = TokenRoundFactory.create_batch(7)
        self.token = TokenFactory(active_round=self.token_round)

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        # Test response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")
        # Test context
        self.assertEqual(response.context["token"], self.token)
        self.assertQuerysetEqual(
            response.context["token_rounds"], TokenRound.objects.all()
        )

    def test_get_anon(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.url}")


class DashboardTokenViewTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.url = reverse("dashboard:token", kwargs={"username": self.user.username})
        self.form_data = {
            "token_amount": "10",
            "token_price_usdt": "1.23",
        }
        self.form_data_invalid = {
            "token_amount": "-1",
            "token_price_usdt": "invalid",
        }

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/token.html")

    def test_get_anon(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.url}")

    def test_post_valid_form(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("dashboard:token", kwargs={"username": self.user.username}),
        )

    def test_post_invalid_form(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.form_data_invalid)
        self.assertEqual(response.status_code, 200)
        form = response.context["buy_token_form"]
        self.assertTrue(form.errors)

    def test_post_anon(self):
        response = self.client.post(self.url, self.form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.url}")


class DashboardTeamViewTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.url = reverse("dashboard:team", kwargs={"username": self.user.username})

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/team.html")

    def test_get_anon(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.url}")


class DashboardProfileViewTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.url = reverse("dashboard:profile", kwargs={"username": self.user.username})

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/profile.html")

    def test_get_anon(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.url}")


class AvatarUpdateViewTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.url = reverse("dashboard:avatar_update")

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_post_avatar_form(self):
        self.client.force_login(self.user)
        # read mock image
        avatar = "test_avatar.jpg"
        image = SimpleUploadedFile(
            name=avatar,
            content=open(f"prm/dashboard/tests/assets/{avatar}", "rb").read(),
            content_type="image/jpeg",
        )
        data = {"avatar": image}
        response = self.client.post(self.url, data)
        self.user.refresh_from_db()
        # tests
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"avatar_url": f"/media/avatars/{avatar}"})
        self.assertEqual(self.user.avatar, f"avatars/{avatar}")

    def test_post_avatar_form_invalid(self):
        self.client.force_login(self.user)
        # read mock image
        data = {"avatar": ""}
        response = self.client.post(self.url, data)
        response_json = response.json()
        self.user.refresh_from_db()
        # tests
        self.assertEqual(response.status_code, 400)
        self.assertTrue(isinstance(response_json["error"], list))
        self.assertEqual(self.user.avatar, "avatars/default.png")

    def test_post_avatar_form_anon(self):
        data = {"avatar": ""}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.url}")
