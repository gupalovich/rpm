from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .utils import calculate_rounded_total_price, get_token

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
        verbose_name="Активный раунд",
    )
    # Fields
    name = models.CharField("Название", max_length=50, default="Token")
    total_amount = models.PositiveBigIntegerField("Всего токенов")
    updated_at = models.DateTimeField("Последнее обновление", auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.active_round.unit_price}"

    @property
    def available_amount(self) -> int:
        return round(self.total_amount * 0.4)

    available_amount.fget.short_description = "Токенов в продаже"


class TokenRound(models.Model):
    class Meta:
        verbose_name = _("Token Round")
        verbose_name_plural = _("Token Rounds")
        ordering = ["unit_price"]

    class Currency(models.TextChoices):
        USD = "$", "USD"

    name = models.CharField("Название", max_length=50, default="# Раунд")
    percent_share = models.PositiveSmallIntegerField("Доля")
    currency = models.CharField(
        "Валюта", max_length=5, choices=Currency.choices, default=Currency.USD
    )
    unit_price = models.DecimalField("Цена", max_digits=6, decimal_places=3)
    total_amount = models.PositiveBigIntegerField("Токенов в раунде", default=0)
    total_amount_sold = models.PositiveIntegerField("Продано в раунде", default=0)
    is_active = models.BooleanField("Активен", default=False)
    is_complete = models.BooleanField("Завершен", default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.unit_price}"

    def clean(self):
        if self.unit_price <= 0:
            raise ValidationError({"unit_price": "Цена не может быть меньше 0."})

    def save(self, *args, **kwargs) -> None:
        self.set_total_amount()
        return super().save(*args, **kwargs)

    @property
    def total_cost(self) -> int:
        """Цена токенов за весь раунд"""
        return round(self.unit_price * self.total_amount)

    @property
    def progress(self) -> float | int:
        """Подсчитать прогресс текущего раунда в процентах"""
        if self.total_amount:
            return round((self.total_amount_sold / self.total_amount) * 100, 2)
        return 0

    @property
    def available_amount(self) -> int:
        """Количество оставшихся токенов в раунде"""
        return self.total_amount - self.total_amount_sold

    def set_total_amount(self) -> None:
        """Подсчитать число токенов в раунде на основе Token.total_amount"""
        if self.total_amount:
            return
        token = get_token()
        if token:
            self.total_amount = round(token.total_amount * (self.percent_share / 100))

    def set_total_amount_sold(self) -> None:
        """На основе транзакций раунда, подсчитать кол-во проданных токенов"""
        self.total_amount_sold = self.transactions.aggregate(
            total=models.Sum("amount")
        )["total"]


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
    amount = models.PositiveIntegerField("Количество")
    total_price = models.DecimalField(
        "Цена токенов", max_digits=10, decimal_places=2, default=0
    )
    reward = models.PositiveIntegerField("Награда", blank=True, null=True)
    reward_sent = models.BooleanField("Награда начислена", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.username} - {self.amount} - {self.total_price}"

    def save(self, *args, **kwargs):
        self.set_total_price()
        self.set_reward()
        return super().save(*args, **kwargs)

    def set_total_price(self) -> None:
        if self.total_price:
            return
        self.total_price = calculate_rounded_total_price(
            unit_price=self.token_round.unit_price, amount=self.amount
        )

    def set_reward(self) -> None:
        if self.buyer.parent:
            self.reward = round(self.amount * (5 / 100))
        else:
            self.reward = 0
