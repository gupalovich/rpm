from collections.abc import Sequence
from typing import Any

from django.contrib.auth import get_user_model
from factory import Faker, post_generation
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    username = Faker("user_name")
    email = Faker("email")
    first_name = Faker("name")
    last_name = Faker("name")
    phone_number = Faker("phone_number")
    date_of_birth = Faker("date_of_birth")
    city = Faker("city")
    metamask_wallet = "0xEFE417C9e02f8B36f7969af9e4c40a25Bed74ecF"

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

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]
