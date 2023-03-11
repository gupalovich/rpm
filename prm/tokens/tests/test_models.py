import random
import re
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
        self.assertIsInstance(token.available_amount, int)
        self.assertTrue(token.updated_at)

    def test_str(self):
        token = TokenFactory()
        self.assertEqual(str(token), f"{token.name} - {token.active_round.unit_price}")

    def test_available_amount(self):
        token = TokenFactory()
        result = round(token.total_amount * 0.4)
        self.assertEqual(token.available_amount, result)


class TokenRoundTests(TestCase):
    def setUp(self) -> None:
        """TODO: test methods/properties"""
        self.batch_size = 5

    def test_create(self):
        TokenRoundFactory.create_batch(self.batch_size)
        self.assertEqual(TokenRound.objects.count(), 5)

    def test_update(self):
        new_price = Decimal("0.01")
        token_round = TokenRoundFactory()
        token_round.unit_price = new_price
        token_round.save()
        token_round.refresh_from_db()
        # Tests
        self.assertEqual(token_round.unit_price, new_price)

    def test_delete(self):
        token_round = TokenRoundFactory()
        token_round.delete()
        self.assertFalse(TokenRound.objects.count())

    def test_fields(self):
        token_round = TokenRoundFactory()
        self.assertTrue(re.match(r"^\d Раунд$", token_round.name))
        self.assertTrue(token_round.percent_share)
        self.assertEqual(token_round.currency, "$")
        self.assertIsInstance(token_round.unit_price, Decimal)
        self.assertEqual(token_round.total_amount, 0)
        self.assertEqual(token_round.total_amount_sold, 0)
        self.assertIsInstance(token_round.is_active, bool)
        self.assertIsInstance(token_round.is_complete, bool)
        self.assertTrue(token_round.updated_at)

    def test_str(self):
        token_round = TokenRoundFactory()
        self.assertEqual(
            str(token_round),
            f"{token_round.name} - {token_round.unit_price}",
        )

    def test_clean(self):
        token_round = TokenRoundFactory(unit_price=0)
        with self.assertRaises(ValidationError):
            token_round.clean()


class TokenTransactionTests(TestCase):
    def setUp(self) -> None:
        """TODO: test methods"""
        self.batch_size = 5
        self.token_amount = random.randrange(100, 40000000)
        self.user = UserFactory(username="PARENT")
        self.user_1 = UserFactory(username="CHILD", parent=self.user)
        self.user_2 = UserFactory(username="CHILD 2", parent=self.user)
        self.token_round = TokenRoundFactory()

    def test_create(self):
        TokenTransactionFactory.create_batch(self.batch_size)
        self.assertEqual(TokenTransaction.objects.count(), 5)

    def test_update(self):
        transaction = TokenTransactionFactory()
        transaction.amount = self.token_amount
        transaction.save()
        transaction.refresh_from_db()
        # Tests
        self.assertEqual(transaction.amount, self.token_amount)

    def test_delete(self):
        transaction = TokenTransactionFactory()
        transaction.delete()
        self.assertFalse(TokenTransaction.objects.count())

    def test_fields(self):
        transaction = TokenTransactionFactory(
            buyer=self.user, token_round=self.token_round
        )
        self.assertEqual(transaction.buyer, self.user)
        self.assertEqual(transaction.token_round, self.token_round)
        self.assertTrue(transaction.amount)
        self.assertFalse(transaction.reward)
        self.assertIsInstance(transaction.reward_sent, bool)
        self.assertTrue(transaction.created_at)

    def test_str(self):
        transaction = TokenTransactionFactory()
        self.assertEqual(
            str(transaction),
            f"{transaction.buyer.username} - {transaction.amount} - {transaction.total_cost}",
        )

    def test_save(self):
        transaction = TokenTransactionFactory()
        # Test default
        self.assertFalse(transaction.reward)
        # Test reward updated
        transaction.buyer = self.user_1  # user with parent
        transaction.save()
        self.assertTrue(transaction.reward)
        self.assertFalse(transaction.reward_sent)

    def test_total_cost(self):
        transaction = TokenTransactionFactory(
            token_round=self.token_round, amount=self.token_amount
        )
        self.assertEqual(
            transaction.token_round.unit_price * transaction.amount,
            transaction.total_cost,
        )

    def test_calc_reward(self):
        """TODO: more cases"""
        transaction = TokenTransactionFactory(
            buyer=self.user_1, token_round=TokenRoundFactory(), amount=self.token_amount
        )
        result = round(transaction.amount * (5 / 100))
        self.assertEqual(transaction.calc_reward, result)

    def test_calc_reward_zero(self):
        transaction = TokenTransactionFactory(
            buyer=self.user, token_round=TokenRoundFactory(), amount=self.token_amount
        )
        self.assertEqual(transaction.calc_reward, 0)
