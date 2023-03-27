from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from prm.core.selectors import get_token
from prm.core.utils import (
    calculate_rounded_total_price, 
    hex_to_dec, 
    hex_to_text,
    hex_to_metamask,
)

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
    def progress(self) -> int | float:
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


class TokenTransactionRaw(models.Model):
    class Meta:
        verbose_name = _("Token Transaction Raw")
        verbose_name_plural = _("Token Transactions Raw")
        ordering = ["-time_stamp"]
        unique_together = ('transaction_hash', 'log_index')
        
    class BlockChain(models.TextChoices):
        BSCSCAN = "bscscan", _("bscscan")

    address = models.CharField(max_length=100)
    topics = ArrayField(
        models.CharField(max_length=100),
        size=4
    )
    data = models.TextField()
    block_number = models.CharField(max_length=100)
    block_hash = models.CharField(max_length=66)
    time_stamp = models.DateTimeField()
    gas_price = models.CharField(max_length=100)
    gas_used = models.CharField(max_length=100)
    log_index = models.CharField(max_length=100)
    transaction_hash = models.CharField(max_length=66, db_index=True)
    transaction_index = models.CharField(max_length=100)
    block_chain = models.CharField(
        db_index=True,
        max_length=20,
        choices=BlockChain.choices,
        default=BlockChain.BSCSCAN,
    )

class TokenTransaction(models.Model):
    class Meta:
        verbose_name = _("Token Transaction")
        verbose_name_plural = _("Token Transactions")
        ordering = ["-created_at"]
        unique_together = ('tx_hash', 'tx_log_index')

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
    buyer_address = models.CharField(db_index=True, max_length=70)
    tx_log_index = models.IntegerField()
    tx_hash = models.CharField(db_index=True, unique=True, editable=False, max_length=70)
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
    created_at = models.DateTimeField("Создана в")

    def __str__(self):
        return f"{self.buyer.username if self.buyer else self.buyer_address} - {self.amount} - {self.total_price}"

    def save(self, *args, **kwargs):
        self.set_total_price()
        return super().save(*args, **kwargs)

    def set_total_price(self) -> None:
        if self.total_price:
            return
        self.total_price = calculate_rounded_total_price(
            unit_price=self.token_round.unit_price, amount=self.amount
        )

    def set_reward(self) -> None:
        """
        TODO: remove hard-coded reward percentage
        """
        if self.buyer and self.buyer.parent:  # self.buyer for null cases
            self.reward = round(self.amount * (5 / 100))
        else:
            self.reward = 0


@receiver(post_save, sender=TokenTransactionRaw)
def create_token_transaction(sender, instance: TokenTransactionRaw, **kwargs): 
    if len(instance.data) < 98:
        return
    
    try:
        func_name = hex_to_text(instance.data[-96:]).strip()
    except UnicodeDecodeError:
        return

    if "buyToken" in func_name:
        token = get_token()
        buyer_address = hex_to_metamask(instance.data[64:128])
        buyer = User.objects.filter(
            metamask_wallet=buyer_address).first()
        token_transaction = TokenTransaction(**{
            "tx_hash": instance.transaction_hash,
            "tx_log_index": instance.log_index,
            "buyer": buyer,
            "buyer_address": buyer_address,
            "token_round": token.active_round,
            "amount": int(instance.data[128:192], base=16),
            "status": TokenTransaction.Status.SUCCESS,
            "created_at": instance.time_stamp,
        }).save()
    elif "rewardToken" in func_name:
        token_transaction = TokenTransaction.objects.filter(
            tx_hash=instance.transaction_hash
        ).first()
        token_transaction.reward_sent = True
        token_transaction.reward = round(hex_to_dec(instance.data[128:192]) * (5 / 100))
        token_transaction.save()

@receiver(post_save, sender=TokenTransaction)
def create_token_transaction(sender, instance: TokenTransaction, **kwargs): 
    if instance.buyer:    
        if instance.reward_sent:
            instance.buyer.parent.update_token_balance(instance.reward)
            return
        
        instance.buyer.update_token_balance(instance.amount)