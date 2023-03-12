from collections.abc import Sequence
from typing import Any

from django.contrib.auth import get_user_model
from factory import Faker, LazyFunction, fuzzy, post_generation
from factory.django import DjangoModelFactory
from faker import Faker as _Faker

fake = _Faker()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]

    username = Faker("user_name")
    email = Faker("email")
    first_name = LazyFunction(lambda: fake.first_name())
    last_name = LazyFunction(lambda: fake.last_name())
    phone_number = Faker("phone_number")
    token_balance = LazyFunction(lambda: fake.random_int(min=0, max=100000))
    metamask_wallet = "0xEFE417C9e02f8B36f7969af9e4c40a25Bed74ecF"
    metamask_confirmed = fuzzy.FuzzyChoice([True, False])

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    @post_generation
    def settings(self, create: bool, extracted: Sequence[Any], **kwargs):
        self.settings.city = fake.city()
        self.settings.birthday = fake.date_of_birth(minimum_age=18, maximum_age=70)
        self.settings.save()
