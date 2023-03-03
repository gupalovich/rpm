from django.core.exceptions import ValidationError
from django.test import TestCase

from ..validators import validate_phone_number


class ValidatePhoneNumberTestCase(TestCase):
    def setUp(self):
        self.valid_phones = ["8 (999) 999-99-99"]
        self.invalid_phones = [
            "8 999 999-99-99",
            "8 999 999 99 99",
            "8 (999) 999 99 99",
            "89999999999",
        ]

    def test_valid_phone_number(self):
        for phone in self.valid_phones:
            validate_phone_number(phone)

    def test_invalid_phone_number(self):
        for phone in self.invalid_phones:
            with self.assertRaises(ValidationError):
                validate_phone_number(phone)
