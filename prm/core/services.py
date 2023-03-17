from django.db.models import Sum

from .selectors import get_token


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
        token_round.save()


def set_next_active_token_round():
    """Переключить раунд на следующий на основе возрастания token_round.unit_price"""
    token = get_token()
    token_round = token.active_round

    if token_round.available_amount <= 0 and token_round.total_amount_sold:
        from prm.tokens.models import TokenRound

        next_round = TokenRound.objects.filter(
            unit_price__gt=token_round.unit_price
        ).first()
        if next_round:
            token.active_round = next_round
            token.save()


def user_update_token_balance(*, user, amount: int):
    """Обновить баланс токенов пользователя"""
    if not isinstance(amount, int):
        return
    user.token_balance += amount
    user.save()
