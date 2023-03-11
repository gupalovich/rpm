from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .validators import validate_phone_number


class User(AbstractUser):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )
    # fields
    phone_number = models.CharField(
        _("Номер телефона"),
        max_length=30,
        blank=True,
        validators=[validate_phone_number],
    )
    avatar = models.ImageField(
        _("Аватар"), upload_to="avatars/", default="avatars/default.png"
    )
    # wallet
    token_balance = models.PositiveIntegerField(_("Баланс токенов"), default=0)
    metamask_wallet = models.CharField(_("Metamask"), max_length=150, blank=True)
    metamask_confirmed = models.BooleanField(_("Metamask подтвержден"), default=False)

    def get_absolute_url(self):
        return reverse("dashboard:index", kwargs={"username": self.username})

    def clean(self):
        if self.parent == self:
            raise ValidationError({"parent": _("Parent and Child cannot be the same.")})

    def token_balance_sum(self):
        """TODO"""


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    birthday = models.DateField(_("Дата рождения"), blank=True, null=True)
    city = models.CharField(_("Город"), max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username}'s settings"
