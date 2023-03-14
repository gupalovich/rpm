import random
import re
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from prm.core.utils import calculate_rounded_total_price

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
        self.assertTrue(token_round.updated_at)

    def test_str(self):
        token_round = TokenRoundFactory()
        self.assertEqual(
            str(token_round),
            f"{token_round.name} - {token_round.unit_price}",
        )

    def test_clean_unit_price(self):
        token_round = TokenRoundFactory(unit_price=0)
        with self.assertRaises(ValidationError):
            token_round.clean()

    def test_clean_total_amount_sold(self):
        token = TokenFactory()
        token_round = token.active_round
        token_round.save()  # set_total_amount
        new_total_amount_sold = token.active_round.total_amount
        # Test can set total_amount_sold == total_amount
        token_round.total_amount_sold = new_total_amount_sold
        token_round.clean()
        # Test can't set total_amount_sold > total_amount
        with self.assertRaises(ValidationError):
            token_round.total_amount_sold = new_total_amount_sold + 1
            token_round.clean()

    def test_save(self):
        token = TokenFactory()
        token_round = TokenRoundFactory(total_amount=0)
        # Test set_total_amount() on save works
        self.assertEqual(
            token_round.total_amount,
            round(token.total_amount * (token_round.percent_share / 100)),
        )

    def test_property_total_cost(self):
        token_round = TokenRoundFactory(total_amount=10000000)
        self.assertEqual(
            token_round.total_cost,
            round(token_round.unit_price * token_round.total_amount),
        )

    def test_property_progress(self):
        token_round = TokenRoundFactory(total_amount=10000000, total_amount_sold=10000)
        token_round_1 = TokenRoundFactory(total_amount=0)
        # Tests
        self.assertEqual(
            token_round.progress,
            round((token_round.total_amount_sold / token_round.total_amount) * 100, 2),
        )
        self.assertEqual(token_round_1.progress, 0)

    def test_property_available_amount(self):
        token_round = TokenRoundFactory(total_amount=10000000, total_amount_sold=10000)
        self.assertEqual(
            token_round.available_amount,
            token_round.total_amount - token_round.total_amount_sold,
        )

    def test_set_total_amount(self):
        token_round = TokenRoundFactory(total_amount=0)
        token = TokenFactory()
        # Tests
        self.assertEqual(token_round.total_amount, 0)
        token_round.set_total_amount()
        self.assertEqual(
            token_round.total_amount,
            round(token.total_amount * (token_round.percent_share / 100)),
        )


class TokenTransactionTests(TestCase):
    def setUp(self) -> None:
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
        self.assertTrue(transaction.total_price)
        self.assertEqual(transaction.status, TokenTransaction.Status.PENDING)
        self.assertFalse(transaction.reward)
        self.assertIsInstance(transaction.reward_sent, bool)
        self.assertTrue(transaction.created_at)

    def test_str(self):
        transaction = TokenTransactionFactory()
        self.assertEqual(
            str(transaction),
            f"{transaction.buyer.username} - {transaction.amount} - {transaction.total_price}",
        )

    def test_save_set_total_price(self):
        transaction = TokenTransactionFactory(total_price=0)
        transaction_1 = TokenTransactionFactory(total_price=1.11)
        self.assertTrue(transaction.total_price > 0)
        self.assertEqual(transaction_1.total_price, 1.11)

    def test_save_set_reward(self):
        transaction = TokenTransactionFactory()
        transaction_1 = TokenTransactionFactory(buyer=self.user_1)
        # Test transaction reward without parent
        self.assertFalse(transaction.reward)
        self.assertFalse(transaction.reward_sent)
        # Test transaction reward with parent
        self.assertTrue(transaction_1.reward)
        self.assertFalse(transaction_1.reward_sent)

    def test_set_total_price(self):
        transaction = TokenTransactionFactory(
            token_round=self.token_round, amount=self.token_amount
        )
        result = calculate_rounded_total_price(
            unit_price=transaction.token_round.unit_price, amount=transaction.amount
        )
        # Set total price
        transaction.set_total_price()
        # Test total_price updated
        self.assertEqual(result, transaction.total_price)

    def test_set_reward(self):
        transaction = TokenTransactionFactory(
            buyer=self.user_1,
            token_round=TokenRoundFactory(),
            amount=self.token_amount,
        )
        result = round(transaction.amount * (5 / 100))
        transaction.set_reward()
        # Test that reward was set
        self.assertEqual(transaction.reward, result)
        self.assertFalse(transaction.reward_sent)

    def test_set_reward_no_parent(self):
        transaction = TokenTransactionFactory(
            buyer=self.user,
            token_round=TokenRoundFactory(),
            amount=self.token_amount,
        )
        transaction.set_reward()
        # Test that reward wasn't set
        self.assertEqual(transaction.reward, 0)
        self.assertFalse(transaction.reward_sent)
