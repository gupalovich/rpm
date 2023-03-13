from decimal import ROUND_HALF_UP, Decimal

import pytest

from prm.users.tests.factories import UserFactory

from ..utils import calculate_rounded_total_price, create_transaction, get_token
from .factories import TokenFactory


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


@pytest.mark.django_db
def test_create_transaction():
    user = UserFactory()
    token = TokenFactory()
    transaction = create_transaction(buyer=user, token_amount=100)
    assert transaction.buyer == user
    assert transaction.token_round == token.active_round
    assert transaction.total_price