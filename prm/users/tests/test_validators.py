from django.apps import apps
from django.core.exceptions import ValidationError
from django.test import TestCase

from ..validators import validate_phone_number, validate_profanity


class ValidatePhoneNumberTests(TestCase):
    def setUp(self):
        self.valid_phones = ["8 (999) 999-99-99"]
        self.invalid_phones = [
            "8 999 999-99-99",
            "8 999 999 99 99",
            "8 (999) 999 99 99",
            "89999999999",
        ]

    def test_valid(self):
        for phone in self.valid_phones:
            validate_phone_number(phone)

    def test_invalid(self):
        for phone in self.invalid_phones:
            with self.assertRaises(ValidationError):
                validate_phone_number(phone)


class ValidateUsernameTests(TestCase):
    def setUp(self):
        apps.get_app_config("users")
        self.valid_usernames = [
            "test_user",
            "test_user_1",
            "abon3153",
            "assessary",
            "admi",
            "mana",
            "sashka007",
        ]
        self.invalid_usernames = ["admin", "manager", "ass", "@admin555", "a-d-m-i-n"]

    def test_valid(self):
        for username in self.valid_usernames:
            validate_profanity(username)

    def test_invalid(self):
        for username in self.invalid_usernames:
            with self.assertRaises(ValidationError, msg=f"For username [{username}]"):
                validate_profanity(username)
