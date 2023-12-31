from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..forms import UserAdminCreationForm, UserSignupForm
from .factories import UserFactory

User = get_user_model()


class UserSignupFormTests(TestCase):
    def setUp(self):
        self.form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "8 (999) 999-99-99",
            "email": "johndoe@example.com",
            "username": "johndoe",
            "password1": "Nh4L9gES$_-Y7cL",
            "password2": "Nh4L9gES$_-Y7cL",
        }
        self.form_data_invalid = {
            "phone_number": "8 999 999-99-99",
            "email": "test@example",
            "username": "test",
            "password1": "password",
            "password2": "test",
        }
        self.url = reverse("account_signup")

    def test_form_valid(self):
        form = UserSignupForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = UserSignupForm(data=self.form_data_invalid)
        # test errors
        self.assertEqual(len(form.errors), 5)
        self.assertEqual(form.errors["first_name"], ["This field is required."])
        self.assertEqual(form.errors["last_name"], ["This field is required."])
        self.assertEqual(form.errors["email"], ["Enter a valid email address."])
        self.assertEqual(form.errors["password1"], ["This password is too common."])
        self.assertEqual(
            form.errors["phone_number"],
            ["Номер телефона должен быть в формате: '8 (999) 999-99-99'."],
        )

    def test_get_referral_field_populated(self):
        """Test url /accounts/signup/?referral=admin populates referral value"""
        referral_value = "admin"
        response = self.client.get(self.url + f"?referral={referral_value}")
        form = response.context["form"]
        self.assertIsInstance(form, UserSignupForm)
        self.assertEqual(form.initial["referral"], referral_value)

    def test_post_valid(self):
        response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse("account_email_verification_sent"))
        # get created user
        user = User.objects.get(username=self.form_data["username"])
        # test created user data
        self.assertEqual(user.parent, None)
        self.assertEqual(user.first_name, self.form_data["first_name"])
        self.assertEqual(user.last_name, self.form_data["last_name"])
        self.assertEqual(user.phone_number, self.form_data["phone_number"])
        self.assertEqual(user.email, self.form_data["email"])
        self.assertEqual(user.username, self.form_data["username"])

    def test_post_invalid(self):
        response = self.client.post(self.url, data={})
        self.assertTemplateUsed(response, "account/signup.html")
        self.assertFalse(User.objects.all())

    def test_post_with_referral_valid(self):
        parent = UserFactory()
        self.form_data.update({"referral": parent.username})
        # make POST request
        response = self.client.post(self.url, data=self.form_data)
        user = User.objects.get(username=self.form_data["username"])
        # test created user data
        self.assertRedirects(response, reverse("account_email_verification_sent"))
        self.assertEqual(user.parent, parent)

    def test_post_with_referral_invalid(self):
        self.form_data.update({"referral": "123"})
        # make POST request
        response = self.client.post(self.url, data=self.form_data)
        user = User.objects.get(username=self.form_data["username"])
        # test created user data
        self.assertRedirects(response, reverse("account_email_verification_sent"))
        self.assertEqual(user.parent, None)


class TestUserAdminCreationForm:
    """
    Test class for all tests related to the UserAdminCreationForm
    """

    def test_username_validation_error_msg(self, user: User):
        """
        Tests UserAdminCreation Form's unique validator functions correctly by testing:
            1) A new user with an existing username cannot be added.
            2) Only 1 error is raised by the UserCreation Form
            3) The desired error message is raised
        """

        # The user already exists,
        # hence cannot be created.
        form = UserAdminCreationForm(
            {
                "username": user.username,
                "password1": user.password,
                "password2": user.password,
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "username" in form.errors
        assert form.errors["username"][0] == _("This username has already been taken.")
