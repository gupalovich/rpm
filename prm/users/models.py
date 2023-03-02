from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    phone_number = models.CharField(
        _("Номер телефона"),
        max_length=30,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?\d{1,3}[\d\s-]{5,}$",
                message='Phone number must be in the format "+999 999-9999".',
            )
        ],
    )
    date_of_birth = models.DateField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to="avatars/", default="avatars/default.png")
    metamask_wallet = models.CharField(max_length=155, blank=True)

    def get_absolute_url(self):
        return reverse("dashboard:index", kwargs={"username": self.username})
