import re

from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from .apps import UsersConfig


def validate_phone_number(value: str) -> None:
    phone_regex = re.compile(r"^8 \(\d{3}\) \d{3}-\d{2}-\d{2}$")
    if not phone_regex.match(value):
        raise ValidationError(
            _("Номер телефона должен быть в формате: '8 (999) 999-99-99'.")
        )


def validate_profanity(word: str) -> None:
    """
    Проверка на запрещенные слова.
    Проверка сценариев:
        1. Изначальное значение
        2. Только буквенное значение
    """
    usernames = [
        word,
        re.sub(r"[^a-zA-Z]", "", word),
    ]
    for username in usernames:
        contains_profanity = UsersConfig.profanity_words.intersection({username})
        if contains_profanity:
            raise ValidationError(_("Имя пользователя запрещенно."))
