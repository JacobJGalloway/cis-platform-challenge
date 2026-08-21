# DECISIONS.md

One entry per fix. Keep each to a short screenful. This is our ADR-lite — the reasoning is the
deliverable, so the next engineer inherits the decision instead of rediscovering it.

---

## ADR-002 — Crew pay dispatch can't double-pay a work order (TICKET-002)

**Context.** `dispatch_pay()` in `app/domains/crewpay/service.py` did a read-then-write: check
`_already_dispatched(...)`, then append a `pay.dispatched` event. Nothing at the data layer stopped
a second dispatched event for the same `(work_order_id, pay_run_id)` — the check only ever prevents
a *sequential* re-call from double-paying; a race between the check and the write (a retried
request, a concurrent call) can still produce two. Separately, the amount used for dispatch was
`requested[0].amount_usd` — picked before checking whether other `pay.requested` events for the same
key disagreed, so a conflicting duplicate request could get silently auto-paid at whichever amount
happened to be first.

**The two options.**
- _Convenient:_ widen the `if _already_dispatched()` check, add an in-process lock, or dedupe in
  reporting after the fact. All three still allow the write; they just make the bad write less
  likely or paper over it downstream. A lock only protects against races within one process — it
  does nothing for two API replicas, and reporting-layer dedupe means the double payment already
  left the building before anyone notices.
- _Structural:_ make the second write impossible to construct. In Postgres: a partial unique index
  on `crewpay.pay_events (work_order_id, pay_run_id) WHERE event_type = 'pay.dispatched'`
  (migration `0002`) — the database itself rejects the second row. In the seed's in-memory store
  (kept in-memory intentionally so tests run DB-less): a dict keyed by `(work_order_id,
  pay_run_id)` written via `setdefault`, so a key can hold exactly one dispatched event regardless
  of how many times or how closely together the write is attempted — no check to race past, because
  there's nothing to check; the losing call's event is simply never the one stored. For conflicting
  `pay.requested` amounts: compute the distinct amount set *before* any amount is chosen, and if
  it's not a singleton, route both conflicting events to a keyed (also insert-if-absent) human
  review queue and dispatch nothing — no arbitrary "first one wins."

**Decision.** Structural on both fronts. The dispatch idempotency has to live in the write itself
(DB constraint in production, key-uniqueness in the DB-less seed store) because any check-then-write
shape is racy by construction, no matter how careful the check. The conflicting-amount case has to
resolve to "neither record is valid" rather than "pick one," because picking one silently commits
money to a number nobody has confirmed correct.

**Invariant restored.** At most one `pay.dispatched` event can ever exist for a given
`(work_order_id, pay_run_id)` — enforced by a DB partial unique index in production and by
key-uniqueness of the in-memory store in this seed — and a work order with disagreeing requested
amounts is never auto-paid; both requests are held in the review queue until a human resolves them.

**Consequences / trade-offs.** `DispatchResult.amount_usd` is now optional (`None` on the flagged
path) — any caller that assumed it was always a number needs updating; there were none yet in this
slice. The review queue is in-memory in the seed and has no resolution/removal API — a human
resolving a conflict in production needs a real queue table and an endpoint to clear an entry, which
is out of scope here. Deferred: persisting `_REVIEW_QUEUE` and building the resolution flow —
trigger: before this ships past the seed slice.
