from django.core.exceptions import ValidationError
from django.test import TestCase

from prm.tokens.tests.factories import TokenFactory

from ..validators import validate_available_tokens


class ValidateAvailableTokensTests(TestCase):
    def setUp(self):
        self.token = TokenFactory()
        self.token.active_round.save()
        self.amount = self.token.active_round.available_amount

    def test_valid(self):
        validate_available_tokens(self.amount)

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            validate_available_tokens(self.amount + 1)
