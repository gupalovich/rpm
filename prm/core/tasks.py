from datetime import datetime

from django.conf import settings
import requests

from config import celery_app
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
    def hex_to_dec(hex):
        if len(hex) <= 2:
            return 0
        return int(hex[2:], base=16)
    
    last_transaction = TokenTransactionRaw.objects.first()
    events_list = requests.get(f"{settings.BSCSCAN_DOMAIN}/api", params={
        "module": "logs",
        "action": "getLogs",
        "fromBlock": last_transaction.block_number if last_transaction else 0,
        "address": settings.BSCSCAN_CONTRACT_ADDRESS,
        "apikey": settings.BSCSCAN_API_KEY
        }, headers={'User-Agent': 'PostmanRuntime/7.29.2'}).json()["result"][1:]
    
    for event in events_list:
        data = {}
        data["address"] = event["address"]
        data["topics"] = event["topics"]
        data["data"] = event["data"]
        data["block_number"] = hex_to_dec(event["blockNumber"])
        data["block_hash"] = event["blockHash"]
        data["time_stamp"] = datetime.fromtimestamp(hex_to_dec(event["timeStamp"]))
        data["gas_price"] = hex_to_dec(event["gasPrice"])
        data["gas_used"] = hex_to_dec(event["gasUsed"])
        data["log_index"] = hex_to_dec(event["logIndex"])
        data["transaction_hash"] = event["transactionHash"]
        data["transaction_index"] = hex_to_dec(event["transactionIndex"])      
        TokenTransactionRaw(**data).save()
    print(f"{len(events_list)} Events added")