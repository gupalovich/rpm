from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .validators import validate_phone_number


class User(AbstractUser):
    phone_number = models.CharField(
        _("Номер телефона"),
        max_length=30,
        blank=True,
        validators=[validate_phone_number],
    )
    date_of_birth = models.DateField(_("Дата рождения"), blank=True, null=True)
    city = models.CharField(_("Город"), max_length=50, blank=True)
    avatar = models.ImageField(
        _("Аватар"), upload_to="avatars/", default="avatars/default.png"
    )
    metamask_wallet = models.CharField(_("Metamask"), max_length=155, blank=True)

    def get_absolute_url(self):
        return reverse("dashboard:index", kwargs={"username": self.username})
