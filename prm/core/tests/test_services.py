from django.db.models import Sum
from django.test import TestCase

from prm.tokens.tests.factories import (
    TokenFactory,
    TokenRoundFactory,
    TokenTransaction,
    TokenTransactionFactory,
    UserFactory,
)

from ..services import (
    MetamaskService,
    create_transaction,
    set_next_active_token_round,
    update_active_round_total_amount_sold,
)
from ..utils import calculate_rounded_total_price


class ServiceTests(TestCase):
    def setUp(self) -> None:
        pass

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
            self.assertEqual(trans.status, TokenTransaction.Status.PENDING)
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
            3, token_round=token_round, status=TokenTransaction.Status.SUCCESS
        )
        TokenTransactionFactory.create_batch(
            3, token_round=token_round, status=TokenTransaction.Status.PENDING
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

    def test_set_next_active_token_round(self):
        """
        Тест смены раунда по средству увеличения unit_price раунда.
        Очередность теста указана в {names}, где ячейка - имя, индекс
        """
        names = [("SECOND", 5), ("THIRD", 4), ("FORTH", 2)]
        token_rounds = [
            TokenRoundFactory(name="FIRST", unit_price="0.001"),
            TokenRoundFactory(name="IGNORED", unit_price="0.001"),
            TokenRoundFactory(name="FORTH", unit_price="0.01"),
            TokenRoundFactory(name="IGNORED", unit_price="0.001"),
            TokenRoundFactory(name="THIRD", unit_price="0.005"),
            TokenRoundFactory(name="SECOND", unit_price="0.002"),
        ]
        token = TokenFactory(active_round=token_rounds[0])

        self.assertEqual(token.active_round.name, "FIRST")

        for name, i in names:
            # Set token round available_amount = 0
            token.active_round.save()  # set_total_amount on save
            token.active_round.total_amount_sold = token.active_round.total_amount
            token.active_round.save()
            self.assertEqual(token.active_round.available_amount, 0)
            # set next round
            set_next_active_token_round()
            token.refresh_from_db()
            # test next round
            self.assertEqual(token.active_round, token_rounds[i])
            self.assertEqual(token.active_round.name, name)

    def test_set_next_active_token_round_ignored(self):
        """
        Проверить, что если token.active_round.available_amount > 0, раунд не будет изменен
        """

        token_rounds = [
            TokenRoundFactory(unit_price="0.001"),
            TokenRoundFactory(unit_price="0.002"),
        ]
        token = TokenFactory(active_round=token_rounds[0])
        active_round = token.active_round
        active_round.save()
        active_round.refresh_from_db()
        # Test nothing changed - coz active_round.available_amount not <= 0
        set_next_active_token_round()
        self.assertTrue(token.active_round.total_amount > 0)
        self.assertEqual(token.active_round, active_round)


class MetamaskServiceTests(TestCase):
    def setUp(self) -> None:
        self.address = "0x123abc"
        self.user = UserFactory(
            phone_number="8 (999) 999-99-99",
            metamask_wallet="",
            metamask_confirmed=False,
        )

    def test_verify_signature_invalid(self):
        is_valid = MetamaskService.verify_signature(
            account_address=self.address,
            signature=self.address,
            csrf_token=self.address,
        )
        self.assertFalse(is_valid)

    def test_confirm_user_wallet(self):
        # update wallet info
        MetamaskService.confirm_user_wallet(
            user=self.user, account_address=self.address
        )
        self.user.refresh_from_db()
        # test confirmed
        self.assertEqual(self.user.metamask_wallet, self.address)
        self.assertTrue(self.user.metamask_confirmed)

    def test_confirm_user_wallet_already_confirmed(self):
        self.user.metamask_confirmed = True
        self.user.save()
        # update wallet info
        MetamaskService.confirm_user_wallet(
            user=self.user, account_address=self.address
        )
        self.user.refresh_from_db()
        # test confirmed
        self.assertEqual(self.user.metamask_wallet, "")
        self.assertTrue(self.user.metamask_confirmed)

    def test_confirm_user_wallet_wallet_not_empty(self):
        self.user.metamask_wallet = self.address
        self.user.save()
        # update wallet info
        MetamaskService.confirm_user_wallet(user=self.user, account_address="123")
        self.user.refresh_from_db()
        # test confirmed
        self.assertEqual(self.user.metamask_wallet, "123")
        self.assertTrue(self.user.metamask_confirmed)
