import pytest
from celery.result import EagerResult

from prm.tokens.tests.factories import TokenFactory

from ..tasks import (
    set_next_active_token_round_task,
    update_active_round_total_amount_sold_task,
)


@pytest.mark.django_db
def test_update_active_round_total_amount_sold_task(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    TokenFactory()
    result = update_active_round_total_amount_sold_task.delay()
    assert isinstance(result, EagerResult)


@pytest.mark.django_db
def test_set_next_active_token_round_task(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    TokenFactory()
    result = set_next_active_token_round_task.delay()
    assert isinstance(result, EagerResult)
