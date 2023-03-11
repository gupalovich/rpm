from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .factories import (
    Token,
    TokenFactory,
    TokenRound,
    TokenRoundFactory,
    TokenTransaction,
    TokenTransactionFactory,
    UserFactory,
)


class TokenTests(TestCase):
    def setUp(self) -> None:
        self.batch_size = 5

    def test_create(self):
        TokenFactory.create_batch(self.batch_size)
        self.assertEqual(Token.objects.count(), 5)

    def test_update(self):
        new_amount = int("400 000 000".replace(" ", ""))
        token = TokenFactory()
        token.total_amount = new_amount
        token.save()
        token.refresh_from_db()
        # Tests
        self.assertEqual(token.total_amount, new_amount)

    def test_delete(self):
        token = TokenFactory()
        token.delete()
        self.assertFalse(Token.objects.count())

    def test_fields(self):
        token = TokenFactory()
        self.assertTrue(token.active_round.unit_price)
        self.assertTrue(token.name)
        self.assertIsInstance(token.total_amount, int)
        self.assertIsInstance(token.total_amount_sold, int)
        self.assertIsInstance(token.total_amount_left, int)
        self.assertTrue(token.updated_at)

    def test_str(self):
        token = TokenFactory()
        self.assertEqual(str(token), f"{token.name} - {token.active_round.unit_price}")

    def test_total_amount_left(self):
        token = TokenFactory(total_amount=400000, total_amount_sold=11111)
        self.assertEqual(
            token.total_amount - token.total_amount_sold, token.total_amount_left
        )
