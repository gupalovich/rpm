from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from prm.tokens.models import Token, TokenRound, TokenTransaction
from prm.users.models import User


@receiver([post_save], sender=User)
def cache_invalidate_user(*args, **kwargs):
    cache.clear()


@receiver([post_save], sender=Token)
def cache_invalidate_token(*args, **kwargs):
    cache.clear()


@receiver([post_save], sender=TokenRound)
def cache_invalidate_token_rounds(*args, **kwargs):
    cache.clear()


@receiver([post_save], sender=TokenTransaction)
def cache_invalidate_token_transactions(*args, **kwargs):
    cache.clear()
