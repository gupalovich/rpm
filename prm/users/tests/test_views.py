from django.test import TestCase
from django.urls import reverse

from ..views import UserSignupView


class UserSignupViewTests(TestCase):
    def setUp(self) -> None:
        self.url = reverse("account_signup")

    def test_get(self):
        response = self.client.get(self.url)
        form = response.context["form"]
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/signup.html")
        self.assertIsInstance(form, UserSignupView.form_class)
