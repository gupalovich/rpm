from config import celery_app

from .services import set_next_active_token_round, update_active_round_total_amount_sold


@celery_app.task()
def update_active_round_total_amount_sold_task():
    update_active_round_total_amount_sold()


@celery_app.task()
def set_next_active_token_round_task():
    set_next_active_token_round()
