from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Sum

from .selectors import get_token, get_token_rounds, get_user_transactions
from .utils import calculate_rounded_total_price

User = get_user_model()
CACHE_TTL = settings.CACHE_TTL


def create_transaction(*, buyer, token_amount):
    from prm.tokens.models import TokenTransaction

    token = get_token()
    transaction = TokenTransaction.objects.create(
        buyer=buyer,
        token_round=token.active_round,
        amount=token_amount,
    )
    return transaction


def update_active_round_total_amount_sold():
    """
    На основе транзакций раунда, подсчитать кол-во проданных токенов, для success транзакций
    """
    token = get_token()
    token_round = token.active_round
    amount_sold = token_round.transactions.filter(status="success").aggregate(
        total=Sum("amount")
    )["total"]
    if amount_sold:
        token_round.total_amount_sold = amount_sold
        token_round.full_clean()
        token_round.save()


def set_next_active_token_round():
    """Переключить раунд на следующий по уровню возрастания token_round.unit_price"""
    token = get_token()
    token_round = token.active_round

    if token_round.available_amount <= 0 and token_round.total_amount_sold:
        from prm.tokens.models import TokenRound

        next_round = TokenRound.objects.filter(
            unit_price__gt=token_round.unit_price
        ).first()
        if next_round:
            token.active_round = next_round
            token.full_clean()
            token.save()


class MetamaskService:
    @staticmethod
    def verify_signature(
        *, account_address: str, signature: str, original_message: str
    ) -> bool:
        """Верификация подписи метамаск и кошелька пользователя

        Args:
            request (HttpRequest): джанго POST-запрос
            account_address (str): Публичный адресс кошелька метамаск
            signature (str): Подпись запроса
            original_message (str): Соль подписи. Обычно это csrf_token.

        TODO: test valid case
        """
        from eth_utils.exceptions import ValidationError

        try:
            from eth_account.messages import defunct_hash_message
            from web3.auto import w3

            # defunct hash
            message_hash = defunct_hash_message(text=original_message)
            signer = w3.eth.account.recoverHash(message_hash, signature=signature)

            if signer == account_address:
                return True
            return False
        except (TypeError, ValidationError):
            return False

    @staticmethod
    def confirm_user_wallet(*, user: User, account_address: str) -> None:
        """Обновить metamask_wallet и metamask_confirmed пользователя

        Args:
            user (User): User instance
            account_address (str): Metamask account_address
        """
        if user.metamask_confirmed:
            return
        user.metamask_wallet = account_address
        user.metamask_confirmed = True
        user.full_clean()
        user.save()


class CacheService:
    @staticmethod
    def get_token():
        token = cache.get("token")
        if token is None:
            token = get_token()
            cache.set("token", token, CACHE_TTL)
            cache.set(
                "token_active_round",
                token.active_round,
                CACHE_TTL,
            )
        return token

    @staticmethod
    def get_token_active_round():
        return cache.get("token_active_round")

    @staticmethod
    def get_token_rounds():
        return cache.get_or_set("token_rounds", get_token_rounds, CACHE_TTL)

    @staticmethod
    def get_user_balance(user: User, token):
        username = user.username
        return cache.get_or_set(
            f"user_{username}_balance",
            lambda: calculate_rounded_total_price(
                unit_price=user.token_balance,
                amount=token.active_round.unit_price,
            ),
            CACHE_TTL,
        )

    @staticmethod
    def get_user_transactions(user: User):
        username = user.username
        return cache.get_or_set(
            f"user_{username}_transactions",
            lambda: get_user_transactions(user=user),
            CACHE_TTL,
        )

    @staticmethod
    def get_user_children(user: User):
        username = user.username
        return cache.get_or_set(
            f"user_{username}_children",
            lambda: user.children.select_related("settings"),
            CACHE_TTL,
        )
