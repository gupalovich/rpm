from decimal import ROUND_HALF_UP, Decimal

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
    progress = models.FloatField("Прогресс раунда", default=0)
    is_active = models.BooleanField("Активен", default=False)
    is_complete = models.BooleanField("Завершен", default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.unit_price}"

    def clean(self):
        if self.unit_price <= 0:
            raise ValidationError({"unit_price": "Цена не может быть меньше 0."})

    def save(self, *args, **kwargs) -> None:
        if not self.total_amount:
            self.total_amount = self.calc_total_amount()
        return super().save(*args, **kwargs)

    @property
    def total_cost(self) -> Decimal:
        """Цена раунда на основе оставшихся токенов"""
        total = Decimal(str(self.unit_price)) * Decimal(str(self.total_amount_left))
        return total.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

    @property
    def total_amount_left(self):
        """Количество оставшихся токенов в раунде"""
        return self.total_amount - self.total_amount_sold

    def calc_total_amount(self) -> int:
        """Подсчитать число токенов в раунде на основе Token.total_amount"""
        token = Token.objects.first()
        if token:
            return round(token.total_amount * (self.percent_share / 100))
        return 0

    def calc_total_amount_sold(self) -> int:
        """На основе транзакций раунда, подсчитать кол-во проданных токенов"""
        return self.transactions.aggregate(total=models.Sum("amount"))["total"]

    def calc_progress(self) -> float:
        """Подсчитать прогресс текущего раунда в процентах"""
        if self.total_amount:
            return round((self.total_amount_sold / self.total_amount) * 100, 2)
        return 0.0


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
    reward = models.PositiveIntegerField("Награда", blank=True, null=True)
    reward_sent = models.BooleanField("Награда начислена", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.username} - {self.amount} - {self.total_cost}"

    def save(self, *args, **kwargs):
        self.reward = self.calc_reward
        return super().save(*args, **kwargs)

    @property
    def total_cost(self) -> Decimal:
        """
        TODO: рефактор в поле, т.к. если token_round изменен цена будет пересчитана неправильно
                Подумать хорошенько
        Цена транзакции в USD
        """
        total = Decimal(str(self.token_round.unit_price)) * Decimal(str(self.amount))
        return total.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

    @property
    def calc_reward(self) -> int:
        if self.buyer.parent:
            return round(self.amount * (5 / 100))
        return 0
