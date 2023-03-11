from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Token(models.Model):
    class Meta:
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

    # Relations
    active_round = models.ForeignKey(
        "TokenRound",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("Активный раунд"),
    )
    # Fields
    name = models.CharField(
        _("Название"), unique=True, db_index=True, max_length=50, default="Token"
    )
    total_amount = models.PositiveBigIntegerField(_("Всего токенов"))
    total_amount_sold = models.PositiveBigIntegerField(_("Продано токенов"), default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.active_round.unit_price}"

    @property
    def total_amount_left(self):
        return self.total_amount - self.total_amount_sold


class TokenRound(models.Model):
    class Meta:
        verbose_name = _("Token Round")
        verbose_name_plural = _("Token Rounds")
        ordering = ["unit_price"]

    class Currency(models.TextChoices):
        USD = "$", "USD"

    name = models.CharField(_("Название"), max_length=50, default=_("# Раунд"))
    currency = models.CharField(
        _("Валюта"), max_length=5, choices=Currency.choices, default=Currency.USD
    )
    unit_price = models.DecimalField(_("Цена"), max_digits=6, decimal_places=3)
    total_cost = models.PositiveIntegerField(_("Цена за все"))
    total_amount_sold = models.PositiveIntegerField(_("Продано в раунде"), default=0)
    percent_share = models.PositiveSmallIntegerField(_("Доля"))
    is_active = models.BooleanField(_("Активен"), default=False)
    is_complete = models.BooleanField(_("Завершен"), default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.unit_price} - {self.total_cost}"

    def clean(self):
        if self.unit_price <= 0:
            raise ValidationError({"unit_price": _("Price can't be less then 0.")})

    @property
    def full_name(self):
        return f"{self.name} {self.percent_share}"

    @property
    def progress(self):
        pass


class TokenTransaction(models.Model):
    class Meta:
        verbose_name = _("Token Transaction")
        verbose_name_plural = _("Token Transactions")
        ordering = ["-created_at"]

    # Relations
    buyer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Покупатель",
    )
    token_round = models.ForeignKey(
        TokenRound,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Раунд",
    )
    # Fields
    amount = models.PositiveIntegerField(_("Количество"))
    reward = models.PositiveIntegerField(_("Награда"), blank=True, null=True)
    reward_sent = models.BooleanField(_("Награда начислена"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.username} - {self.amount} - {self.price_sum}"

    def save(self, *args, **kwargs):
        self.reward = self.calc_reward(self.buyer.parent)
        return super().save(*args, **kwargs)

    @property
    def price_sum(self):
        return round(self.token_round.unit_price * self.amount, 2)

    def calc_reward(self, parent: User) -> int:
        if parent:
            reward_percent = 5
            return round(self.amount * (reward_percent / 100))
        return 0
