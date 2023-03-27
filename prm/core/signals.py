from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from prm.tokens.models import Token, TokenRound, TokenTransaction
from prm.users.models import User


@receiver([post_save], sender=Token)
def cache_invalidate_token(*args, **kwargs):
    cache.delete_many(["token", "token_active_round", "token_rounds"])


@receiver([post_save], sender=TokenRound)
def cache_invalidate_token_rounds(*args, **kwargs):
    cache.delete_many(["token", "token_active_round", "token_rounds"])


@receiver([post_save], sender=User)
def cache_invalidate_user(*args, **kwargs):
    username = kwargs["instance"].username
    cache.delete_many(
        [
            f"user_{username}_balance",
            f"user_{username}_transactions",
            f"user_{username}_children",
        ]
    )


@receiver([post_save], sender=TokenTransaction)
def cache_invalidate_user_transactions(*args, **kwargs):
    user = kwargs["instance"].buyer
    if user:
        username = user.username
        cache.delete(f"user_{username}_transactions")
