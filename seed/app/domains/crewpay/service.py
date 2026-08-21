"""Crew Pay service (Bookkeeping / Crew Manager domain).

Pay events are an append-only stream. To pay a crew for a work order we look up the pending
`pay.requested` event(s) for that work order and pay run, then append a `pay.dispatched` event.
"""

from __future__ import annotations

from app.domains.crewpay.schemas import DispatchResult, PayEvent

# In-memory stand-in for the append-only crewpay.pay_events table (loaded from the fixture).
_EVENTS: list[PayEvent] = []


def load_events(events: list[PayEvent]) -> None:
    _EVENTS.extend(events)


def _already_dispatched(work_order_id: str, pay_run_id: str) -> bool:
    return any(
        e.event_type == "pay.dispatched"
        and e.work_order_id == work_order_id
        and e.pay_run_id == pay_run_id
        for e in _EVENTS
    )


async def dispatch_pay(work_order_id: str, pay_run_id: str) -> DispatchResult:
    """Dispatch pay for a work order in a pay run.

    Finds the requested amount and appends a dispatched event.
    """
    requested = [
        e
        for e in _EVENTS
        if e.event_type == "pay.requested"
        and e.work_order_id == work_order_id
        and e.pay_run_id == pay_run_id
    ]
    if not requested:
        raise LookupError(f"No pending pay for {work_order_id} in {pay_run_id}")

    if _already_dispatched(work_order_id, pay_run_id):
        return DispatchResult(
            work_order_id=work_order_id,
            pay_run_id=pay_run_id,
            amount_usd=requested[0].amount_usd,
            status="already_dispatched",
        )

    amount = requested[0].amount_usd
    _EVENTS.append(
        PayEvent(
            event_id=f"EVT-{len(_EVENTS) + 9000}",
            work_order_id=work_order_id,
            pay_run_id=pay_run_id,
            crew_id=requested[0].crew_id,
            event_type="pay.dispatched",
            amount_usd=amount,
            labor_code=requested[0].labor_code,
            occurred_at="2026-07-28T16:00:00Z",
        )
    )
    return DispatchResult(
        work_order_id=work_order_id,
        pay_run_id=pay_run_id,
        amount_usd=amount,
        status="dispatched",
    )
