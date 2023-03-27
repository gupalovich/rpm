from datetime import datetime

from django.conf import settings
import requests

from config import celery_app

from prm.core.utils import hex_to_dec, clean_hex
from prm.tokens.models import TokenTransactionRaw
from .services import set_next_active_token_round, update_active_round_total_amount_sold


@celery_app.task()
def update_active_round_total_amount_sold_task():
    update_active_round_total_amount_sold()


@celery_app.task()
def set_next_active_token_round_task():
    set_next_active_token_round()


@celery_app.task()
def transactions_pooling():
    last_transaction = TokenTransactionRaw.objects.first()
    events_list = requests.get(f"{settings.BSCSCAN_DOMAIN}/api", params={
        "module": "logs",
        "action": "getLogs",
        "fromBlock": last_transaction.block_number if last_transaction else 0,
        "address": settings.BSCSCAN_CONTRACT_ADDRESS,
        "apikey": settings.BSCSCAN_API_KEY
        }, headers={'User-Agent': 'PostmanRuntime/7.29.2'}).json()["result"]
    
    for event in events_list:
        if last_transaction and last_transaction.transaction_hash == clean_hex(event["transactionHash"]):
            continue
        data = {}
        data["address"] = clean_hex(event["address"])
        data["topics"] = event["topics"]
        data["data"] = clean_hex(event["data"])
        data["block_number"] = hex_to_dec(event["blockNumber"])
        data["block_hash"] = clean_hex(event["blockHash"])
        data["time_stamp"] = datetime.fromtimestamp(hex_to_dec(event["timeStamp"]))
        data["gas_price"] = hex_to_dec(event["gasPrice"])
        data["gas_used"] = hex_to_dec(event["gasUsed"])
        data["log_index"] = hex_to_dec(event["logIndex"])
        data["transaction_hash"] = clean_hex(event["transactionHash"])
        data["transaction_index"] = hex_to_dec(event["transactionIndex"])      
        TokenTransactionRaw.objects.create(**data)
        # TODO: Add logging