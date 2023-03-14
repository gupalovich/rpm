from django.test import TestCase

from prm.tokens.tests.factories import TokenFactory, TokenTransaction, UserFactory

from ..services import create_transaction, get_token
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
