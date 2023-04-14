import json

from django.db.models import Sum
from django.conf import settings
from web3 import Web3
from web3.middleware import geth_poa_middleware

from prm.core.utils import hex_remove_zeros
from prm.tokens.models import TokenTransaction


def recalculate_user_balance(user):
    # cleaned_wallet = str(hex_remove_zeros(user.metamask_wallet)).lower()
    TokenTransaction.objects.filter(buyer_address=user.metamask_wallet).update(
        buyer=user
    )
    sum_tokens = TokenTransaction.objects.filter(
        buyer_address=user.metamask_wallet
    ).aggregate(Sum("amount"), Sum("reward"))

    user.token_balance = 0
    user.update_token_balance(sum_tokens["amount__sum"])
    if user.parent:
        user.parent.update_token_balance(sum_tokens["reward__sum"])


def set_parent_in_smart(user):
    w3 = Web3(Web3.HTTPProvider(settings.BSCSCAN_HTTP_PROVIDER))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    abi = json.loads(settings.ABI_CONTRACT)
    contract = w3.eth.contract(
        address=Web3.toChecksumAddress(settings.BSCSCAN_CONTRACT_ADDRESS), abi=abi
    )
    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(settings.BSCSCAN_PRIVATE_WALLET_ADDRESS))

    tx = contract.functions.setParent(
        Web3.toChecksumAddress(user.metamask_wallet),
        Web3.toChecksumAddress(user.parent.metamask_wallet),
    ).buildTransaction(
        {
            "chainId": 97,
            "gas": 100000,
            "gasPrice": w3.toWei("10", "gwei"),
            "nonce": nonce,
        }
    )
    sign_tx = w3.eth.account.sign_transaction(tx, settings.BSCSCAN_PRIVATE_KEY)
    w3.eth.sendRawTransaction(sign_tx.rawTransaction)
