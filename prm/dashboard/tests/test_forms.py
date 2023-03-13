from datetime import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from prm.users.tests.factories import UserFactory

from ..forms import AvatarUpdateForm, BuyTokenForm, ProfileUserUpdateForm


class BuyTokenFormTests(TestCase):
    def test_form_valid(self):
        form = BuyTokenForm(data={"token_amount": 1111})
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = BuyTokenForm(data={"token_amount": "abc", "token_price_usdt": "1.23.45"})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)

    def test_token_amount_required(self):
        form = BuyTokenForm(data={"token_price_usdt": 1.2345})
        self.assertFalse(form.is_valid())
        self.assertTrue("token_amount" in form.errors)

    def test_token_amount_clean_negative(self):
        form = BuyTokenForm(data={"token_amount": -10})
        self.assertFalse(form.is_valid())
        self.assertTrue("token_amount" in form.errors)


class AvatarUpdateFormTests(TestCase):
    def setUp(self):
        base_path = "prm/dashboard/tests/assets"
        self.avatar_path = f"{base_path}/test_avatar.jpg"
        self.avatar_sm_path = f"{base_path}/test_avatar_sm.jpg"
        self.avatar_lg_path = f"{base_path}/test_avatar_lg.jpg"

    def test_valid_form(self):
        # create a fake image file to upload
        file_data = open(self.avatar_path, "rb").read()
        uploaded_file = SimpleUploadedFile(
            "image.jpg", file_data, content_type="image/jpeg"
        )
        form_data = {"avatar": uploaded_file}
        form = AvatarUpdateForm(data=form_data, files=form_data)
        self.assertTrue(form.is_valid())

    def test_empty_form(self):
        form_data = {}
        form = AvatarUpdateForm(data=form_data, files=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)

    def test_invalid_image_sm(self):
        # create a fake image file that is too small to pass the validator
        file_data = open(self.avatar_sm_path, "rb").read()
        uploaded_file = SimpleUploadedFile(
            "small_image.jpg", file_data, content_type="image/jpeg"
        )
        form_data = {"avatar": uploaded_file}
        form = AvatarUpdateForm(data=form_data, files=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)

    def test_invalid_image_lg(self):
        # create a fake image file that is too small to pass the validator
        file_data = open(self.avatar_lg_path, "rb").read()
        uploaded_file = SimpleUploadedFile(
            "large_image.jpg", file_data, content_type="image/jpeg"
        )
        form_data = {"avatar": uploaded_file}
        form = AvatarUpdateForm(data=form_data, files=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)


class ProfileUserUpdateFormTests(TestCase):
    def setUp(self):
        self.user_pass = "testpass123"
        self.user = UserFactory(password=self.user_pass)
        self.form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "testuser@example.com",
            # "phone_number": "8 (999) 999-99-99",
            "birthday": "1990-01-01",
            "city": "Test City",
            "metamask_wallet": "0x1234567890",
            "password": "newpass123",
            "password1": "newpass123",
        }
        self.url = reverse("dashboard:profile", kwargs={"username": self.user.username})

    def test_valid_data(self):
        form = ProfileUserUpdateForm(
            data=self.form_data,
            instance=self.user,
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.first_name, self.form_data["first_name"])
        self.assertEqual(user.last_name, self.form_data["last_name"])
        # self.assertEqual(user.phone_number, self.form_data["phone_number"])
        self.assertEqual(
            user.settings.birthday,
            datetime.strptime(self.form_data["birthday"], "%Y-%m-%d").date(),
        )
        self.assertEqual(user.settings.city, self.form_data["city"])
        self.assertEqual(user.metamask_wallet, self.form_data["metamask_wallet"])
        self.assertTrue(user.check_password(self.form_data["password"]))

    def test_password_mismatch(self):
        self.form_data.update({"password": "newpass123", "password1": "mismatch"})
        form = ProfileUserUpdateForm(
            data=self.form_data,
            instance=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)

    def test_weak_password(self):
        self.form_data.update({"password": "password", "password1": "password"})
        form = ProfileUserUpdateForm(
            data=self.form_data,
            instance=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_empty_password(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"password": "", "password1": ""})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(""))
        self.assertTrue(self.user.check_password(self.user_pass))
