import re

from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_phone_number(value: str) -> None:
    """TODO: реализовать более человеческую валидацию номера - понизить строгость"""
    phone_regex = re.compile(r"^8 \(\d{3}\) \d{3}-\d{2}-\d{2}$")
    if not phone_regex.match(value):
        raise ValidationError(
            _("Номер телефона должен быть в формате: '8 (999) 999-99-99'.")
        )
