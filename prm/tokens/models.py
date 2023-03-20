import uuid as uuid_lib

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from prm.core.selectors import get_token
from prm.core.utils import calculate_rounded_total_price

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
    unit_price = models.DecimalField(
        "Цена", db_index=True, max_digits=6, decimal_places=3
    )
    total_amount = models.PositiveBigIntegerField("Токенов в раунде", default=0)
    total_amount_sold = models.PositiveIntegerField("Продано в раунде", default=0)
    updated_at = models.DateTimeField("Последнее обновление", auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.unit_price}"

    def clean(self):
        self.clean_unit_price()
        self.clean_total_amount_sold()

    def clean_unit_price(self):
        msg = _("Цена не может быть меньше 0.")
        if self.unit_price <= 0:
            raise ValidationError({"unit_price": msg})

    def clean_total_amount_sold(self):
        msg = _("Кол-во проданных токенов не может быть больше кол-ва токенов в раунде")
        if self.total_amount_sold > self.total_amount:
            raise ValidationError({"total_amount_sold": msg})

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

    progress.fget.short_description = "Прогресс"

    @property
    def available_amount(self) -> int:
        """Количество оставшихся токенов в раунде"""
        return self.total_amount - self.total_amount_sold

    available_amount.fget.short_description = "Токенов в продаже"

    def set_total_amount(self) -> None:
        """Подсчитать число токенов в раунде на основе Token.total_amount"""
        if self.total_amount:
            return
        token = get_token()
        if token:
            self.total_amount = round(token.total_amount * (self.percent_share / 100))


class TokenTransaction(models.Model):
    class Meta:
        verbose_name = _("Token Transaction")
        verbose_name_plural = _("Token Transactions")
        ordering = ["-created_at"]

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        FAILED = "failed", _("Failed")
        SUCCESS = "success", _("Success")

    # Relations
    buyer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Покупатель",
        null=True,
        blank=True,
    )
    token_round = models.ForeignKey(
        TokenRound,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Раунд",
    )
    # Fields
    uuid = models.UUIDField(db_index=True, default=uuid_lib.uuid4, editable=False)
    amount = models.PositiveIntegerField("Количество")
    total_price = models.DecimalField(
        "Цена токенов", max_digits=10, decimal_places=2, default=0
    )
    status = models.CharField(
        "Статус",
        db_index=True,
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reward = models.PositiveIntegerField("Награда", blank=True, null=True)
    reward_sent = models.BooleanField("Награда начислена", default=False)
    created_at = models.DateTimeField("Создана в", auto_now_add=True)

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
        if self.buyer and self.buyer.parent:  # self.buyer for null cases
            self.reward = round(self.amount * (5 / 100))
        else:
            self.reward = 0


class TokenTransactionRaw(models.Model):
    class Meta:
        verbose_name = _("Token Transaction Raw")
        verbose_name_plural = _("Token Transactions Raw")
        ordering = ["-time_stamp"]
        
    class BlockChain(models.TextChoices):
        BSCSCAN = "bscscan", _("bscscan")

    address = models.CharField(max_length=100)
    topics = ArrayField(
        models.CharField(max_length=100),
        size=4
    )
    data = models.CharField(max_length=100)
    block_number = models.CharField(max_length=100)
    block_hash = models.CharField(max_length=66)
    time_stamp = models.DateTimeField()
    gas_price = models.CharField(max_length=100)
    gas_used = models.CharField(max_length=100)
    log_index = models.CharField(max_length=100)
    transaction_hash = models.CharField(max_length=66, unique=True, db_index=True, primary_key=True)
    transaction_index = models.CharField(max_length=100)
    block_chain = models.CharField(
        db_index=True,
        max_length=20,
        choices=BlockChain.choices,
        default=BlockChain.BSCSCAN,
    )