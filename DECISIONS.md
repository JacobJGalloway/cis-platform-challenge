# DECISIONS.md

One entry per fix. Keep each to a short screenful. This is our ADR-lite — the reasoning is the
deliverable, so the next engineer inherits the decision instead of rediscovering it.

---

## ADR-001 — PII-bearing measure docs can't resolve to a non-in-tenant AI provider (TICKET-001)

**Context.** `resolve_provider(capability)` in `app/ai/router.py` picked the first registered
provider offering a capability, ordered by cost/quality only. It had no notion of task sensitivity,
and the public (non-in-tenant) provider was first in preference order — so a `pii_bearing` measure
doc, whose pixel content includes the homeowner's name/address/phone, was routed to a provider
outside the CIS tenant boundary. Extraction "worked," so nothing looked wrong.

**The two options.**
- _Convenient:_ add `if provider.in_tenant:` (or a redact-before-send step) at the call site in
  `ai_review.py`. This "works" for this one call path, but it's a fact a future engineer has to
  remember to re-check on every new caller of `resolve_provider` — a new AI-touching feature that
  copies the router-then-call pattern without also copying the `if` reintroduces the leak, and
  nothing stops it from compiling or passing review at a glance.
- _Structural:_ make sensitivity an input to resolution itself. `resolve_provider(capability, *,
  pii_bearing: bool)` filters non-in-tenant providers out of the eligible set before a candidate is
  ever chosen. A `pii_bearing` task literally cannot resolve to one — there's no `if` to forget
  because there's no path that returns an ineligible provider. Added a `PiiLeakError` tripwire at
  the egress point in `ai_review.py` as defense in depth for a future call path that resolves a
  provider some other way. Added `NoEligibleProviderError`, fail-closed: if no in-tenant provider
  offers the capability, the caller must flag for human review, never fall back to an ineligible one.

**Decision.** Structural. Filtering at resolution is the only version where the violation is
unconstructable rather than merely checked; the egress tripwire is cheap insurance for a mis-wired
future path, not the primary control.

**Invariant restored.** A `pii_bearing` task can never resolve to a provider whose `in_tenant` is
`False` — `resolve_provider` excludes such providers from the eligible set before selection, and
`review_measure_doc` raises `PiiLeakError` if content would reach one anyway.

**Consequences / trade-offs.** If a market/document type needs extraction and no in-tenant provider
is registered for that capability, the doc now goes to `requires_human_review=True` instead of
degrading to the public provider — that's the correct fail-closed behavior, but it means throughput
depends on in-tenant provider coverage. Deferred: alerting/paging when `NoEligibleProviderError`
fires in production, so a coverage gap gets noticed quickly rather than silently piling up in a
human-review queue — trigger: first time this fires outside a test.
