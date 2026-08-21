# TICKET-002: Crew pay can be dispatched twice for the same work order

## Reported
An installer was paid twice for one work order. The pay-request stream contains a duplicate
`pay.requested` for `WO-100841` in pay run `PR-2026-30` (a retry upstream), and a dispatch retry can
append a second `pay.dispatched`.

## Where
- `app/domains/crewpay/service.py` — `dispatch_pay()` does a read-then-write: it checks
  `_already_dispatched(...)` and then appends a `pay.dispatched` event. Nothing at the data layer
  prevents two dispatched events for the same `(work_order_id, pay_run_id)`, and concurrent/retried
  calls race the check.
- `seed/migrations/versions/0001_initial.py` — note: `crewpay.pay_events` has no uniqueness guard on
  dispatched events (called out in the migration comment).

## The precept
> **One-write fan-out + append-only; money operations are idempotent.** Replaying an event or
> retrying a request cannot double-apply. On ambiguity around money, fail closed to a human.

## What we are NOT looking for
A bigger `if` around the check, an in-process lock, or "we'll dedupe in reporting." The double-pay
must be impossible at the write, not merely unlikely.

## What a structural fix looks like
- A **uniqueness constraint** (DB-level) on dispatched pay per `(work_order_id, pay_run_id)` so the
  second write is rejected by the database — idempotent by construction. Add the Alembic migration
  (upgrade + downgrade).
- The service treats a rejected duplicate as a **successful no-op** (`already_dispatched`), not an
  error.
- **Fail-closed on ambiguity:** if the requested events disagree (e.g. two different amounts for the
  same work order + pay run), do **not** pay — flag for a human.

## Definition of done
- A test that **fails on the current code** by double-dispatching `WO-100841` and getting two
  dispatched events / two payments, and **passes on your fix** (exactly one).
- A test proving conflicting-amount requests are flagged, not paid.
- `DECISIONS.md` entry naming the invariant.
