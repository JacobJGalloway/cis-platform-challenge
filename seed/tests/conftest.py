"""Test fixtures. Loads the synthetic crew-pay stream fresh for each test module."""

from __future__ import annotations

import pytest

from app.domains.crewpay import service as pay_service
from app.seed_data import load_pay_events


@pytest.fixture(autouse=True)
def _reset_pay_stream():
    pay_service._EVENTS.clear()
    load_pay_events()
    yield
    pay_service._EVENTS.clear()
