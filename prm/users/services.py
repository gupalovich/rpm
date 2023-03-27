from django.db.models import Sum

from prm.tokens.models import TokenTransaction

def recalculate_user_balance(user):
    TokenTransaction.objects.filter(
            buyer_address=user.metamask_wallet
    ).update(buyer=user)
    print(user.metamask_wallet) 
    sum_tokens = TokenTransaction.objects.filter(
        buyer_address=user.metamask_wallet
    ).aggregate(Sum("amount"), Sum("reward"))
    print(sum_tokens)
    
    user.token_balance = 0
    user.update_token_balance(sum_tokens["amount__sum"])

    user.parent.update_token_balance(sum_tokens["reward__sum"])