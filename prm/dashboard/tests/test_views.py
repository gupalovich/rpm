import json

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse

from prm.core.selectors import get_user_transactions
from prm.core.utils import calculate_rounded_total_price
from prm.tokens.tests.factories import (
    TokenFactory,
    TokenRound,
    TokenRoundFactory,
    TokenTransaction,
    TokenTransactionFactory,
)
from prm.users.tests.factories import UserFactory

CACHE_TTL = settings.CACHE_TTL


class MetamaskConfirmViewTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory(metamask_wallet="", metamask_confirmed=False)
        self.url = reverse("dashboard:metamask_confirm")
        self.wallet = "0x123abc"

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_post(self):
        """Signature logic can't be tested here"""
        data = {"accountAddress": self.wallet, "user": self.user.username}
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Invalid signature"})

    def test_post_unknown_user(self):
        data = {"accountAddress": self.wallet, "user": "test123"}
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)


class DashboardRedirectViewTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.token = TokenFactory()
        self.url = reverse("dashboard:redirect")
        self.url_home = reverse("dashboard:home_redirect")

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.user.get_absolute_url())

    def test_get_anon(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("account_login"))

    def test_get_index(self):
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.user.get_absolute_url())

    def test_get_index_anon(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("account_login"))

    def test_get_home(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url_home)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.user.get_absolute_url())

    def test_get_home_anon(self):
        response = self.client.get(self.url_home)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("account_login"))


class DashboardBaseViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()
        self.children = [
            UserFactory(parent=self.user),
            UserFactory(parent=UserFactory()),
        ]
        self.token_round = TokenRoundFactory()
        self.token_rounds = TokenRoundFactory.create_batch(3)
        self.token = TokenFactory(active_round=self.token_round)
        self.url = reverse("dashboard:index", kwargs={"username": self.user.username})
        self.client.force_login(self.user)

    def test_context_data(self):
        response = self.client.get(self.url)
        user_referral = f"{reverse('account_signup')}?referral={self.user.username}"
        user_balance = calculate_rounded_total_price(
            unit_price=self.user.token_balance,
            amount=self.token.active_round.unit_price,
        )
        user_children = self.user.children.select_related("settings")
        # test context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"], self.user)
        self.assertIn(user_referral, response.context["user_referral_link"])
        self.assertEqual(response.context["user_balance"], user_balance)
        self.assertEqual(len(response.context["user_children"]), 1)
        self.assertQuerysetEqual(response.context["user_children"], user_children)
        self.assertEqual(response.context["token"], self.token)
        self.assertQuerysetEqual(
            response.context["token_rounds"], TokenRound.objects.all()
        )

    def test_context_data_transactions(self):
        response = self.client.get(self.url)
        # create transactions
        TokenTransactionFactory.create_batch(
            3, buyer=self.user, status=TokenTransaction.Status.SUCCESS
        )
        TokenTransactionFactory.create_batch(
            3, buyer=self.user, status=TokenTransaction.Status.PENDING
        )
        TokenTransactionFactory(
            buyer=self.children[0],
            status=TokenTransaction.Status.SUCCESS,
            reward_sent=True,
        )
        TokenTransactionFactory(
            buyer=self.children[1],
            status=TokenTransaction.Status.SUCCESS,
            reward_sent=True,
        )
        # query transactions
        user_transactions = get_user_transactions(user=self.user)
        context_transactions = response.context["user_transactions"]
        self.assertQuerysetEqual(context_transactions, user_transactions)
        self.assertEqual(len(context_transactions), 4)


class DashboardIndexViewTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.token_round = TokenRoundFactory()
        self.token = TokenFactory(active_round=self.token_round)
        self.url = reverse("dashboard:index", kwargs={"username": self.user.username})

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        # Test response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")

    def test_get_anon(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.url}")


class DashboardTokenViewTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.form_data = {
            "token_amount": "10",
            "token_price_usdt": "1.23",
        }
        self.form_data_invalid = {
            "token_amount": "-1",
            "token_price_usdt": "invalid",
        }
        self.token_round = TokenRoundFactory()
        self.token = TokenFactory(active_round=self.token_round)
        self.token.active_round.save()  # set total_amount on active_round
        self.url = reverse("dashboard:token", kwargs={"username": self.user.username})

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        # Test response
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
        self.token = TokenFactory()
        self.url = reverse("dashboard:team", kwargs={"username": self.user.username})

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        # Test response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/team.html")

    # def test_get_caching(self):
    #     self.client.force_login(self.user)
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.headers["Cache-Control"], f"max-age={CACHE_TTL}")
    #     self.assertEqual(response.headers["Vary"], "Cookie, Accept-Language")

    # def test_get_caching_anon(self):
    #     response = self.client.get(self.url)
    #     self.assertFalse(response.headers.get("Cache-Control"))

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
        # Test response
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
