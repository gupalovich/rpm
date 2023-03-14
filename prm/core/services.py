from django.db.models import Sum


def get_token():
    from prm.tokens.models import Token

    return Token.objects.first()


def create_transaction(*, buyer, token_amount):
    from prm.tokens.models import TokenTransaction

    token = get_token()
    transaction = TokenTransaction.objects.create(
        buyer=buyer, token_round=token.active_round, amount=token_amount
    )
    return transaction


def update_active_round_total_amount_sold():
    """На основе транзакций раунда, подсчитать кол-во проданных токенов"""
    token = get_token()
    token_round = token.active_round
    amount_sold = token_round.transactions.filter(status="success").aggregate(
        total=Sum("amount")
    )["total"]
    if amount_sold:
        token_round.total_amount_sold = amount_sold
        token_round.save()
