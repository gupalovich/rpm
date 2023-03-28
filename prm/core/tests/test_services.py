from django.core.cache import cache
from django.db.models import Sum
from django.test import TestCase, override_settings

from prm.tokens.tests.factories import (
    TokenFactory,
    TokenRound,
    TokenRoundFactory,
    TokenTransaction,
    TokenTransactionFactory,
    UserFactory,
)

from ..selectors import get_user_transactions
from ..services import (
    CacheService,
    MetamaskService,
    set_next_active_token_round,
    update_active_round_total_amount_sold,
)
from ..utils import calculate_rounded_total_price


class ServiceTests(TestCase):
    def setUp(self) -> None:
        pass

    def test_update_active_round_total_amount_sold(self):
        token = TokenFactory(active_round=TokenRoundFactory())
        token_round = token.active_round
        token_round.save()
        # Create pending and success batch of transactions
        TokenTransactionFactory.create_batch(
            3,
            amount=1000000,
            token_round=token_round,
            status=TokenTransaction.Status.SUCCESS,
        )
        TokenTransactionFactory.create_batch(
            3, token_round=token_round, status=TokenTransaction.Status.PENDING
        )
        TokenTransactionFactory.create_batch(
            3, token_round=token_round, status=TokenTransaction.Status.FAILED
        )
        # # Update active_round amount
        update_active_round_total_amount_sold()
        token_round.refresh_from_db()
        # # Test result
        amount_sold = token_round.transactions.filter(status="success").aggregate(
            total=Sum("amount")
        )["total"]
        self.assertEqual(token_round.total_amount_sold, amount_sold)
        self.assertEqual(token_round.total_amount_sold, 3000000)

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
            original_message=self.address,
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


class CacheServiceTests(TestCase):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "",
        }
    }

    def setUp(self) -> None:
        self.user = UserFactory()
        self.token = TokenFactory()

    @override_settings(CACHES=CACHES)
    def test_get_token(self):
        key = "token"
        self.assertFalse(cache.get(key))
        # Test cached result
        result = CacheService.get_token()
        self.assertEqual(result, self.token)
        self.assertEqual(cache.get(key), self.token)

    @override_settings(CACHES=CACHES)
    def test_get_token_active_round(self):
        key = "token_active_round"
        self.token.save()  # invalidate cache from test_get_token
        self.assertFalse(cache.get(key))
        # Test cached result
        CacheService.get_token()
        result = CacheService.get_token_active_round()
        self.assertEqual(result, self.token.active_round)
        self.assertEqual(cache.get(key), self.token.active_round)

    @override_settings(CACHES=CACHES)
    def test_get_token_rounds(self):
        key = "token_rounds"
        self.assertFalse(cache.get(key))
        # Test cached result
        TokenRoundFactory.create_batch(5)
        qs = TokenRound.objects.all()
        result = CacheService.get_token_rounds()
        self.assertQuerysetEqual(result, qs)
        self.assertQuerysetEqual(cache.get(key), qs)

    @override_settings(CACHES=CACHES)
    def test_get_user_balance(self):
        key = f"user_{self.user.username}_balance"
        self.assertFalse(cache.get(key))
        # Test cached result
        user_balance = calculate_rounded_total_price(
            unit_price=self.user.token_balance,
            amount=self.token.active_round.unit_price,
        )
        result = CacheService.get_user_balance(self.user, self.token)
        self.assertEqual(result, user_balance)
        self.assertEqual(cache.get(key), user_balance)

    @override_settings(CACHES=CACHES)
    def test_get_user_transactions(self):
        key = f"user_{self.user.username}_transactions"
        self.assertFalse(cache.get(key))
        # Create transactions
        TokenTransactionFactory.create_batch(
            5, buyer=self.user, status=TokenTransaction.Status.SUCCESS
        )
        TokenTransactionFactory.create_batch(2, status=TokenTransaction.Status.SUCCESS)
        # Test cached result
        result = CacheService.get_user_transactions(self.user)
        self.assertEqual(result.count(), 5)
        self.assertQuerysetEqual(result, get_user_transactions(user=self.user))
        self.assertQuerysetEqual(cache.get(key), get_user_transactions(user=self.user))

    @override_settings(CACHES=CACHES)
    def test_get_user_children(self):
        key = f"user_{self.user.username}_children"
        self.assertFalse(cache.get(key))
        # Create children
        UserFactory.create_batch(5, parent=self.user)
        UserFactory.create_batch(2, parent=UserFactory())
        UserFactory.create_batch(2)
        # Test cached result
        qs = self.user.children.select_related("settings")
        result = CacheService.get_user_children(self.user)
        self.assertEqual(result.count(), 5)
        self.assertQuerysetEqual(result, qs)
        self.assertQuerysetEqual(cache.get(key), qs)
