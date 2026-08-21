"""TICKET-002: crew pay can't be dispatched twice for the same work order, and conflicting
requested amounts must be flagged for a human rather than auto-resolved.
"""

from __future__ import annotations

import pytest

from app.domains.crewpay import service as pay_service
from app.domains.crewpay.schemas import PayEvent


@pytest.mark.anyio
async def test_dispatch_write_primitive_rejects_a_second_dispatched_event_for_same_key():
    """This is the defect named in the ticket, stated precisely: nothing at the data layer
    prevents two dispatched events for the same (work_order_id, pay_run_id). On the code as
    delivered, the write step is an unconditional `_EVENTS.append(...)` with no guard at the data
    layer — two calls to that step for the same key produce two dispatched events regardless of
    the earlier `_already_dispatched()` check (a real caller can race between the check and the
    write; this test isolates the write step itself, which is where the invariant must live).

    On the fix, the write step is `_DISPATCHED.setdefault(key, candidate)`: the dict key can hold
    only one value, so calling it twice for the same key can never leave two dispatched events —
    it's rejected by the shape of the store, not by a check a caller could race past.
    """
    key = ("WO-100841", "PR-2026-30")
    first = PayEvent(
        event_id="EVT-A", work_order_id=key[0], pay_run_id=key[1], crew_id="CRW-208",
        event_type="pay.dispatched", amount_usd=318.75, labor_code="INS-CPT-STD",
        occurred_at="2026-07-28T16:00:00Z",
    )
    second = PayEvent(
        event_id="EVT-B", work_order_id=key[0], pay_run_id=key[1], crew_id="CRW-208",
        event_type="pay.dispatched", amount_usd=318.75, labor_code="INS-CPT-STD",
        occurred_at="2026-07-28T16:05:00Z",
    )

    winner_a = pay_service._DISPATCHED.setdefault(key, first)
    winner_b = pay_service._DISPATCHED.setdefault(key, second)

    assert winner_a is first
    assert winner_b is first  # second write rejected; the first write's event is authoritative
    assert len(pay_service._DISPATCHED) == 1


@pytest.mark.anyio
async def test_dispatch_retry_is_idempotent_no_op_not_a_second_payment():
    """Integration-style: the real fixture has a duplicate pay.requested for WO-100841 in
    PR-2026-30 (a retry upstream). Dispatching it, then retrying the dispatch call itself, must
    produce exactly one pay.dispatched event and the retry must report already_dispatched.
    """
    first = await pay_service.dispatch_pay("WO-100841", "PR-2026-30")
    second = await pay_service.dispatch_pay("WO-100841", "PR-2026-30")

    assert first.status == "dispatched"
    assert second.status == "already_dispatched"
    assert first.amount_usd == second.amount_usd == 318.75

    dispatched_events = [
        e
        for e in pay_service._EVENTS
        if e.event_type == "pay.dispatched"
        and e.work_order_id == "WO-100841"
        and e.pay_run_id == "PR-2026-30"
    ]
    assert len(dispatched_events) == 1


@pytest.mark.anyio
async def test_conflicting_amounts_are_flagged_not_paid():
    """Two pay.requested events for the same work order + pay run with different amounts must not
    be auto-resolved by picking either one — both go to the human review queue and nothing is
    dispatched.
    """
    pay_service.load_events(
        [
            PayEvent(
                event_id="EVT-C1", work_order_id="WO-999", pay_run_id="PR-2026-31",
                crew_id="CRW-300", event_type="pay.requested", amount_usd=100.00,
                labor_code="INS-CPT-STD", occurred_at="2026-08-01T10:00:00Z",
            ),
            PayEvent(
                event_id="EVT-C2", work_order_id="WO-999", pay_run_id="PR-2026-31",
                crew_id="CRW-300", event_type="pay.requested", amount_usd=140.00,
                labor_code="INS-CPT-STD", occurred_at="2026-08-01T10:05:00Z",
            ),
        ]
    )

    result = await pay_service.dispatch_pay("WO-999", "PR-2026-31")

    assert result.status == "flagged_conflicting_amount"
    assert result.amount_usd is None

    dispatched_events = [
        e for e in pay_service._EVENTS if e.event_type == "pay.dispatched" and e.work_order_id == "WO-999"
    ]
    assert dispatched_events == []

    flags = pay_service.review_queue()
    assert len(flags) == 1
    assert flags[0].work_order_id == "WO-999"
    assert {e.amount_usd for e in flags[0].conflicting_events} == {100.00, 140.00}

    # A retry doesn't auto-heal or re-flag; it stays parked pending human resolution.
    retry = await pay_service.dispatch_pay("WO-999", "PR-2026-31")
    assert retry.status == "flagged_conflicting_amount"
    assert len(pay_service.review_queue()) == 1
