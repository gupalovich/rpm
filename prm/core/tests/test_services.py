from decimal import ROUND_HALF_UP, Decimal

import pytest

from prm.tokens.tests.factories import TokenFactory

from ..services import get_token
from ..utils import calculate_rounded_total_price


def test_calculate_rounded_total_price_half_up():
    unit_price = 0.001
    amount = 99999
    total = Decimal(str(unit_price)) * Decimal(str(amount))
    result = total.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    assert calculate_rounded_total_price(unit_price=unit_price, amount=amount) == result


@pytest.mark.django_db
def test_get_token():
    assert not get_token()
    tokens = [TokenFactory(), TokenFactory()]
    assert get_token() == tokens[0]
