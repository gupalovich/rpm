from config import celery_app


@celery_app.task(bind=True)
def update_active_round_total_amount_sold(self):
    from .services import update_active_round_total_amount_sold

    update_active_round_total_amount_sold()


@celery_app.task(bind=True)
def update_active_round(self):
    pass
