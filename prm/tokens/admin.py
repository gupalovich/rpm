from django.contrib import admin

from .models import Token, TokenRound, TokenTransaction


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "total_amount",
        "available_amount",
        "updated_at",
    ]


@admin.register(TokenRound)
class TokenRoundAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "unit_price",
        "total_cost",
        "percent_share",
    ]


@admin.register(TokenTransaction)
class TokenTransactionAdmin(admin.ModelAdmin):
    list_display = ["buyer_address", "buyer", "status", "amount", "total_price", "reward", "reward_sent"]
