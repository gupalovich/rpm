from decimal import ROUND_HALF_UP, Decimal


def calculate_rounded_total_price(
    *, unit_price, amount, rounding=ROUND_HALF_UP
) -> Decimal:
    total = Decimal(str(unit_price)) * Decimal(str(amount))
    return total.quantize(Decimal(".01"), rounding=rounding)
