from django.db.models import Q
from django.test import TestCase

from prm.tokens.tests.factories import (
    TokenFactory,
    TokenRound,
    TokenRoundFactory,
    TokenTransaction,
    TokenTransactionFactory,
)
from prm.users.tests.factories import UserFactory

from ..selectors import get_token, get_token_rounds, get_user_transactions


class SelectorsTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.children = [
            UserFactory(parent=self.user),
            UserFactory(parent=UserFactory()),
        ]

    def test_get_token(self):
        self.assertFalse(get_token())
        tokens = [TokenFactory(), TokenFactory()]
        self.assertEqual(get_token(), tokens[0])

    def test_get_token_rounds(self):
        self.assertFalse(get_token_rounds())
        TokenRoundFactory.create_batch(3)
        self.assertQuerysetEqual(get_token_rounds(), TokenRound.objects.all())

    def test_get_user_transactions(self):
        TokenTransactionFactory.create_batch(
            3, buyer=self.user, status=TokenTransaction.Status.SUCCESS
        )
        TokenTransactionFactory.create_batch(
            3, buyer=self.user, status=TokenTransaction.Status.PENDING
        )
        TokenTransactionFactory(
            buyer=self.children[0],
            status=TokenTransaction.Status.SUCCESS,
            reward_sent=True,
        )
        TokenTransactionFactory(
            buyer=self.children[0],
            status=TokenTransaction.Status.SUCCESS,
            reward_sent=False,
        )
        TokenTransactionFactory(
            buyer=self.children[1],
            status=TokenTransaction.Status.SUCCESS,
            reward_sent=True,
        )
        # query transactions
        user_transactions = (
            TokenTransaction.objects.filter(status=TokenTransaction.Status.SUCCESS)
            .select_related("buyer")
            .filter(Q(buyer=self.user) | Q(buyer__parent=self.user, reward_sent=True))
        )
        transactions = get_user_transactions(user=self.user)
        self.assertQuerysetEqual(transactions, user_transactions)
        self.assertEqual(len(transactions), 4)
