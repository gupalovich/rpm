from decimal import ROUND_HALF_UP, Decimal

from ..services import calculate_rounded_total_price


def test_calculate_rounded_total_price_half_up():
    unit_price = 0.001
    amount = 10000
    total = Decimal(str(unit_price)) * Decimal(str(amount))
    result = total.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    assert calculate_rounded_total_price(unit_price=unit_price, amount=amount) == result
