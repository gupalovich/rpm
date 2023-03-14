import pytest
from celery.result import EagerResult

from prm.tokens.tests.factories import TokenFactory

from ..tasks import update_active_round_total_amount_sold


@pytest.mark.django_db
def test_update_active_round_total_amount_sold(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    TokenFactory()
    result = update_active_round_total_amount_sold.delay()
    assert isinstance(result, EagerResult)
