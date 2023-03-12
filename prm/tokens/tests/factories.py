from decimal import Decimal

from factory import LazyAttribute, LazyFunction, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from faker import Faker

from prm.users.tests.factories import UserFactory

from ..models import Token, TokenRound, TokenTransaction

fake = Faker()


class TokenRoundFactory(DjangoModelFactory):
    class Meta:
        model = TokenRound

    name = LazyAttribute(lambda _: f"{fake.random_int(min=1, max=8)} Раунд")
    percent_share = FuzzyChoice(choices=[10, 5, 3, 1])
    unit_price = FuzzyChoice(
        choices=[
            Decimal("0.001"),
            Decimal("0.005"),
            Decimal("0.01"),
            Decimal("0.05"),
            Decimal("0.06"),
            Decimal("0.07"),
            Decimal("0.08"),
            Decimal("0.1"),
        ]
    )
    total_amount = 0
    total_amount_sold = 0


class TokenFactory(DjangoModelFactory):
    class Meta:
        model = Token

    active_round = SubFactory(TokenRoundFactory)
    # Fields
    name = "PRM Token"
    total_amount = 1000000000


class TokenTransactionFactory(DjangoModelFactory):
    class Meta:
        model = TokenTransaction

    buyer = SubFactory(UserFactory)
    token_round = SubFactory(TokenRoundFactory)
    # Fields
    amount = LazyFunction(lambda: fake.random_int(min=100, max=40000000))
    reward = LazyFunction(lambda: fake.random_int(min=0, max=1000))
