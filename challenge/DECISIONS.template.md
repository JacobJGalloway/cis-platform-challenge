# DECISIONS.md

One entry per fix. Keep each to a short screenful. This is our ADR-lite — the reasoning is the
deliverable, so the next engineer inherits the decision instead of rediscovering it.

---

## ADR-00X — <short title> (TICKET-00Y)

**Context.** What the seed code did, and which precept it violated.

**The two options.**
- _Convenient:_ <the guard-on-top fix> — why it "works" and why it's not enough (what can still go
  wrong, who has to remember).
- _Structural:_ <the shape change> — why the violation becomes unconstructable.

**Decision.** Which you chose and why.

**Invariant restored.** One sentence a future engineer inherits, e.g. _"A `pii_bearing` task can never
resolve to a provider whose `in_tenant` is false."_

**Consequences / trade-offs.** What this costs, what you'd revisit, any deferred follow-up with a
named trigger.
