from django.core.cache import cache
from django.test import TestCase, override_settings

from prm.tokens.tests.factories import (
    TokenFactory,
    TokenTransactionFactory,
    UserFactory,
)

from ..services import CacheService


class SignalsTests(TestCase):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "",
        }
    }

    def setUp(self) -> None:
        self.users = [
            UserFactory(username="john"),
            UserFactory(username="test"),
        ]
        self.token = TokenFactory()

    @override_settings(CACHES=CACHES)
    def test_cache_invalidate_token(self):
        # save cache
        CacheService.get_token()
        CacheService.get_token_rounds()
        self.assertTrue(cache.get("token"))
        self.assertTrue(cache.get("token_active_round"))
        self.assertTrue(cache.get("token_rounds"))
        # invalidate cache
        self.token.save()
        self.assertFalse(cache.get("token"))
        self.assertFalse(cache.get("token_active_round"))
        self.assertFalse(cache.get("token_rounds"))

    @override_settings(CACHES=CACHES)
    def test_cache_invalidate_token_rounds(self):
        # save cache
        CacheService.get_token()
        CacheService.get_token_rounds()
        self.assertTrue(cache.get("token"))
        self.assertTrue(cache.get("token_active_round"))
        self.assertTrue(cache.get("token_rounds"))
        # invalidate cache
        self.token.active_round.save()
        self.assertFalse(cache.get("token"))
        self.assertFalse(cache.get("token_active_round"))
        self.assertFalse(cache.get("token_rounds"))

    @override_settings(CACHES=CACHES)
    def test_cache_invalidate_user(self):
        for user in self.users:
            CacheService.get_user_balance(user, self.token)
            CacheService.get_user_transactions(user)
            CacheService.get_user_children(user)
            self.assertTrue(cache.get(f"user_{user.username}_balance") is not None)
            self.assertTrue(cache.get(f"user_{user.username}_transactions") is not None)
            self.assertTrue(cache.get(f"user_{user.username}_children") is not None)
        # Test cache invalidated for user
        user = self.users[0]
        user.save()
        self.assertTrue(cache.get(f"user_{user.username}_balance") is None)
        self.assertTrue(cache.get(f"user_{user.username}_transactions") is None)
        self.assertTrue(cache.get(f"user_{user.username}_children") is None)
        # Test cache was not invalidation for other user
        user = self.users[1]
        self.assertTrue(cache.get(f"user_{user.username}_balance") is not None)
        self.assertTrue(cache.get(f"user_{user.username}_transactions") is not None)
        self.assertTrue(cache.get(f"user_{user.username}_children") is not None)

    @override_settings(CACHES=CACHES)
    def test_cache_invalidate_user_transactions(self):
        user = self.users[0]
        CacheService.get_user_transactions(user)
        self.assertTrue(cache.get(f"user_{user.username}_transactions") is not None)
        # Create transaction from other user
        TokenTransactionFactory(buyer=self.users[1])
        self.assertTrue(cache.get(f"user_{user.username}_transactions") is not None)
        # Invalidate transactions for user
        TokenTransactionFactory(buyer=user)
        self.assertTrue(cache.get(f"user_{user.username}_transactions") is None)
