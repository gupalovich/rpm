from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TokensConfig(AppConfig):
    name = "prm.tokens"
    verbose_name = _("Tokens")
