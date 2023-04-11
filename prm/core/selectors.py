from django.db.models import Q


def get_token():
    from prm.tokens.models import Token

    return Token.objects.first()


def get_token_rounds():
    from prm.tokens.models import TokenRound

    return TokenRound.objects.all()


def get_user_transactions(*, user):
    from prm.tokens.models import TokenTransaction

    user_transactions = (
        TokenTransaction.objects.filter(status=TokenTransaction.Status.SUCCESS)
        .select_related("buyer")
        .filter(
            Q(buyer=user) | Q(buyer__parent=user, reward_sent=True, reward_type="buyer")
        )
    )
    return user_transactions
