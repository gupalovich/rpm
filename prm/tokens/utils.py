from decimal import ROUND_HALF_UP, Decimal


def calculate_rounded_total_price(
    *, unit_price: Decimal, amount: int, rounding=ROUND_HALF_UP
) -> Decimal:
    total = Decimal(str(unit_price)) * Decimal(str(amount))
    return total.quantize(Decimal(".01"), rounding=rounding)


def get_token():
    from .models import Token

    return Token.objects.first()


def create_transaction(*, buyer, token_amount):
    from .models import TokenTransaction

    token = get_token()
    transaction = TokenTransaction.objects.create(
        buyer=buyer, token_round=token.active_round, amount=token_amount
    )
    return transaction
