from django.db.models import Sum
from django.test import TestCase

from prm.tokens.tests.factories import (
    TokenFactory,
    TokenTransaction,
    TokenTransactionFactory,
    UserFactory,
)

from ..services import (
    create_transaction,
    get_token,
    update_active_round_total_amount_sold,
)
from ..utils import calculate_rounded_total_price


class ServiceTests(TestCase):
    def setUp(self) -> None:
        pass

    def test_get_token(self):
        self.assertFalse(get_token())
        tokens = [TokenFactory(), TokenFactory()]
        self.assertEqual(get_token(), tokens[0])

    def test_create_transaction(self):
        token = TokenFactory()
        users = [(UserFactory(), 100), (UserFactory(), 30000000)]
        for user, amount in users:
            create_transaction(buyer=user, token_amount=amount)
        # Test transactions
        transactions = TokenTransaction.objects.order_by("created_at")
        # tests
        self.assertEqual(len(transactions), len(users))
        for i, trans in enumerate(transactions):
            self.assertEqual(trans.buyer, users[i][0])
            self.assertEqual(trans.token_round, token.active_round)
            self.assertEqual(trans.amount, users[i][1])
            self.assertEqual(
                trans.total_price,
                calculate_rounded_total_price(
                    unit_price=token.active_round.unit_price, amount=trans.amount
                ),
            )

    def test_update_active_round_total_amount_sold(self):
        token = TokenFactory()
        token_round = token.active_round
        # Create pending and success batch of transactions
        TokenTransactionFactory.create_batch(
            100, token_round=token_round, status=TokenTransaction.Status.SUCCESS
        )
        TokenTransactionFactory.create_batch(
            100, token_round=token_round, status=TokenTransaction.Status.PENDING
        )
        # Update active_round amount
        update_active_round_total_amount_sold()
        token_round.refresh_from_db()
        # Test result
        amount_sold = token_round.transactions.filter(status="success").aggregate(
            total=Sum("amount")
        )["total"]
        self.assertEqual(token_round.total_amount_sold, amount_sold)
        self.assertIsInstance(token_round.total_amount_sold, int)
