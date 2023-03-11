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
        "is_active",
        "is_complete",
    ]


@admin.register(TokenTransaction)
class TokenTransactionAdmin(admin.ModelAdmin):
    list_display = ["buyer", "amount", "reward", "total_cost"]
