"""Crew Pay service (Bookkeeping / Crew Manager domain).

Pay events are an append-only stream. To pay a crew for a work order we look up the pending
`pay.requested` event(s) for that work order and pay run, then append a `pay.dispatched` event.

This seed keeps the event stream in memory (rather than a live Postgres table) so tests run without
a DB — see `app/seed_data.py`. The in-memory store still enforces the same invariant the real
`crewpay.pay_events` table enforces via a partial unique index (migrations/0002): a dispatched event
for a given (work_order_id, pay_run_id) can exist at most once, by construction of the store itself.
"""

from __future__ import annotations

from app.domains.crewpay.schemas import DispatchResult, PayEvent, PayReviewFlag

# In-memory stand-in for the append-only crewpay.pay_events table (loaded from the fixture).
_EVENTS: list[PayEvent] = []

# Exactly one dispatched event may exist per (work_order_id, pay_run_id) — the key can hold only
# one value, so a second dispatch attempt cannot create a second entry. This is the in-memory
# analogue of the DB's partial unique index, not a check that a caller could bypass.
_DISPATCHED: dict[tuple[str, str], PayEvent] = {}

# Conflicts routed to a human instead of being auto-resolved. Also insert-if-absent: a retried
# dispatch call for an already-flagged key doesn't spawn duplicate queue entries.
_REVIEW_QUEUE: dict[tuple[str, str], PayReviewFlag] = {}


def load_events(events: list[PayEvent]) -> None:
    _EVENTS.extend(events)


def review_queue() -> list[PayReviewFlag]:
    """Conflicts awaiting human resolution."""
    return list(_REVIEW_QUEUE.values())


def _requested_for(work_order_id: str, pay_run_id: str) -> list[PayEvent]:
    return [
        e
        for e in _EVENTS
        if e.event_type == "pay.requested"
        and e.work_order_id == work_order_id
        and e.pay_run_id == pay_run_id
    ]


async def dispatch_pay(work_order_id: str, pay_run_id: str) -> DispatchResult:
    """Dispatch pay for a work order in a pay run.

    Finds the requested amount and appends a dispatched event. If the requested events for this
    key disagree on amount, neither is treated as valid: both go to the human review queue and
    nothing is dispatched. If a dispatched event already exists for this key (a genuine retry),
    that is a successful no-op, not a second payment.
    """
    key = (work_order_id, pay_run_id)

    if key in _REVIEW_QUEUE:
        return DispatchResult(
            work_order_id=work_order_id, pay_run_id=pay_run_id, amount_usd=None,
            status="flagged_conflicting_amount",
        )

    requested = _requested_for(work_order_id, pay_run_id)
    if not requested:
        raise LookupError(f"No pending pay for {work_order_id} in {pay_run_id}")

    distinct_amounts = {e.amount_usd for e in requested}
    if len(distinct_amounts) > 1:
        _REVIEW_QUEUE.setdefault(
            key,
            PayReviewFlag(
                work_order_id=work_order_id,
                pay_run_id=pay_run_id,
                reason="conflicting_amount",
                conflicting_events=tuple(requested),
            ),
        )
        return DispatchResult(
            work_order_id=work_order_id, pay_run_id=pay_run_id, amount_usd=None,
            status="flagged_conflicting_amount",
        )

    candidate = PayEvent(
        event_id=f"EVT-{len(_EVENTS) + 9000}",
        work_order_id=work_order_id,
        pay_run_id=pay_run_id,
        crew_id=requested[0].crew_id,
        event_type="pay.dispatched",
        amount_usd=requested[0].amount_usd,
        labor_code=requested[0].labor_code,
        occurred_at="2026-07-28T16:00:00Z",
    )
    # The single source of truth for "has this been dispatched": whichever call's event wins the
    # insert is the one that actually happened. A losing call never appends to `_EVENTS`.
    stored = _DISPATCHED.setdefault(key, candidate)
    if stored is candidate:
        _EVENTS.append(stored)
        status = "dispatched"
    else:
        status = "already_dispatched"

    return DispatchResult(
        work_order_id=work_order_id, pay_run_id=pay_run_id, amount_usd=stored.amount_usd,
        status=status,
    )
