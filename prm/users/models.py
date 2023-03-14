from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .validators import validate_phone_number


class User(AbstractUser):
    class Meta:
        ordering = ["-date_joined"]

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
        super().clean()
        self.clean_parent()
        self.clean_metamask_wallet()
        self.clean_metamask_wallet_confirmed()

    def clean_parent(self):
        """Validate parent - prevent from parent being it's own child"""
        msg = _("Родитель не может быть рефераллом.")
        if self.parent == self:
            raise ValidationError({"parent": msg})

    def clean_metamask_wallet(self):
        """Validate metamask wallet - ensure that people couldn't modify it if metamask confirmed"""
        msg = _("Metamask подтвержден и не может быть изменен.")
        if self.metamask_wallet:
            user = User.objects.get(pk=self.pk)
            if user.metamask_confirmed != self.metamask_confirmed:
                return
            if user.metamask_wallet and user.metamask_confirmed:
                raise ValidationError({"metamask_wallet": msg})

    def clean_metamask_wallet_confirmed(self):
        """Validation for metamask wallet - ensure that a blank wallet cannot be confirmed"""
        msg = _("Metamask не может быть подтвержден с пустым кошельком.")
        if self.metamask_confirmed and not self.metamask_wallet:
            raise ValidationError({"metamask_wallet": msg})

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    birthday = models.DateField(_("Дата рождения"), blank=True, null=True)
    city = models.CharField(_("Город"), max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username}'s settings"
