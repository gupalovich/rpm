import json

from django.db.models import Sum
from django.conf import settings
from web3 import Web3
from web3.middleware import geth_poa_middleware

from prm.core.utils import hex_remove_zeros
from prm.tokens.models import TokenTransaction


def recalculate_user_balance(user):
    cleaned_wallet = str(hex_remove_zeros(user.metamask_wallet)).lower()
    TokenTransaction.objects.filter(
            buyer_address=cleaned_wallet
    ).update(buyer=user)
    sum_tokens = TokenTransaction.objects.filter(
        buyer_address=cleaned_wallet
    ).aggregate(Sum("amount"), Sum("reward"))

    user.token_balance = 0
    user.update_token_balance(sum_tokens["amount__sum"])
    if user.parent:
        user.parent.update_token_balance(sum_tokens["reward__sum"])

def set_parent_in_smart(user):
    w3 = Web3(Web3.HTTPProvider(settings.BSCSCAN_HTTP_PROVIDER))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    abi = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"_from","type":"address"},{"indexed":false,"internalType":"address","name":"_to","type":"address"},{"indexed":false,"internalType":"uint256","name":"_amount","type":"uint256"},{"indexed":false,"internalType":"string","name":"_func_name","type":"string"}],"name":"EventBuyToken","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"_buyer","type":"address"},{"indexed":false,"internalType":"address","name":"_reward_to","type":"address"},{"indexed":false,"internalType":"uint256","name":"_amount","type":"uint256"},{"indexed":false,"internalType":"string","name":"_func_name","type":"string"}],"name":"EventRewardToken","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_tokenToBuy","type":"uint256"}],"name":"buyToken","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getContractBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_child","type":"address"}],"name":"getParent","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getRoundToDisplay","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getTokenForReward","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getTokenRoundForSale","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getTokenTotalForSale","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_to","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"sendBonusReward","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_child","type":"address"},{"internalType":"address","name":"_parent","type":"address"}],"name":"setParent","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"withdrawAll","outputs":[],"stateMutability":"nonpayable","type":"function"}]')
    contract = w3.eth.contract(address=Web3.to_checksum_address(settings.BSCSCAN_CONTRACT_ADDRESS), abi=abi)
    nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(user.metamask_wallet))

    tx = contract.functions.setParent(
        Web3.to_checksum_address(user.metamask_wallet), 
        Web3.to_checksum_address(user.parent.metamask_wallet)
    ).build_transaction({
        "chainId": 97, "gas": 100000, "gasPrice": w3.to_wei("10", "gwei"), "nonce": nonce
    })
    sign_tx = w3.eth.account.sign_transaction(tx, settings.BSCSCAN_PRIVATE_KEY)
    w3.eth.send_raw_transaction(sign_tx.rawTransaction)