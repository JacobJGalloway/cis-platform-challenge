# PLAN.md

> Commit this file **first**, on its own commit, before any other work. The timestamp is a signal.

## Problem in one paragraph
CIS wants AI to extract room dimensions, product, and square footage from measure documents — but the
homeowner's name, address, and phone number are printed directly on the same field sheet, baked into
the same pixels the extraction model has to read. There is no sanitize-then-extract step, because
sanitizing would also destroy the data we want, and any redaction good enough to fully remove PII from
a rasterized image can't be verified to have worked before the bytes are sent. The actual trap: the
guarantee has to prevent the *call* to a non-in-tenant provider from ever being placed for PII-bearing
content — it can't depend on cleaning the payload first, because there's no reliable "first" for that
cleaning to happen in.

## Architecture / mechanism
The safe path has to be the only path a `pii_bearing` task can type-check into — not a flag someone
remembers to check.

- **Close the sensitivity type.** Replace a loose `sensitivity: str` on the document model with a
  closed `TaskSensitivity` enum (`PII_BEARING` / `NON_PII`). A strongly-typed field can silently default
  to the wrong value or be mistyped; an enum can't.
- **Split resolution by sensitivity, not just capability.** Today's shape — a resolver that takes a
  capability string and returns the first matching provider in preference order — has no way to *know*
  a task is PII-bearing, so it structurally cannot refuse one. The fix: a resolver path reachable only
  for `PII_BEARING` tasks filters the provider registry down to `in_tenant=True` **before** any
  preference ordering runs, and that filtered function is the *only* function a `pii_bearing` call site
  can call. There is no code path inside it that can return a non-in-tenant provider — not because
  someone checked a flag, but because the non-in-tenant providers were never in the candidate set.
- **Egress tripwire as a backstop, not the primary guarantee.** All provider calls pass through one
  chokepoint that asserts `provider.in_tenant is True` for anything tagged `pii_bearing`, and raises
  before bytes leave the process. This exists for the case the type-level gate doesn't cover: a new
  provider registered with a wrong capability flag, or a future call site that reaches a provider
  directly instead of through the gated resolver. It's explicitly the second layer, not the fix itself —
  a tripwire alone is a guard someone could route around; paired with the gate, routing around it
  requires deliberately bypassing both.
- **Boundary vs. data-handling, named explicitly.** "No-training" and "subscription-isolated" describe
  what a provider does with data it already received — they say nothing about whether a human reviewer
  outside the tenant boundary can see it under that provider's default abuse-monitoring. `in_tenant`
  has to mean the bytes never left the boundary, full stop. The gate is keyed on `in_tenant`
  specifically, not on any weaker capability or compliance flag, so a provider can't satisfy the gate by
  being "safe enough" in a different sense.

## Fail-closed behavior
When a `PII_BEARING` `doc_extract` task has no `in_tenant=True` provider capable of it (e.g. the only
provider that handles poor handwriting isn't in-tenant), the task is **not** retried against a
non-in-tenant provider and not silently dropped. It's marked `blocked_needs_human` and written to a
review queue. A person either extracts the document manually or grants a scoped, logged, one-time
exception — the system never decides on its own to relax the boundary. Default if this is never
specified further: block and queue, never auto-fallback to "best available."

## What I don't know yet
- Whether "in-tenant" means the documented AI service boundary alone, or also requires network-layer
  isolation (private endpoint, no public egress) for the request/response path.
- Whether `in_tenant` is a static property of a registered provider, or can vary by region/deployment
  for the same provider — that changes whether the gate belongs on the provider or on the resolved
  deployment.
- Who actually works the human-review queue, and whether that surface needs its own claims-based access
  control.
- How this scales operationally at "thousands of documents, growing daily" — what queue depth is
  acceptable before it becomes a real bottleneck, and who owns that number.

## Clarifying questions (3 sharp ones)
1. **Q:** Does "in-tenant" mean the documented AI service boundary (e.g. Azure AI Document Intelligence,
   Azure OpenAI within our tenant), or does it also require network-layer isolation (private endpoint,
   no public internet egress) for the request/response? — **why it matters:** determines whether a
   provider-identity check is sufficient or whether the egress tripwire also needs to verify the actual
   network path — **my default if unanswered:** the stricter reading — service boundary *and* private
   networking — **what changes:** if network isolation isn't required, the tripwire is a pure
   application-layer assertion; if it is, the tripwire has to inspect the request path, not just which
   provider object made the call.
2. **Q:** Is `in_tenant` fixed per provider, or can the same provider be in-tenant in one
   region/deployment and not another? — **why it matters:** if it varies, the capability can't live as
   a static field on the provider class — it has to be resolved per deployment — **my default if
   unanswered:** treat it as static per registered provider instance — **what changes:** if it varies,
   the gate moves one layer deeper, from provider selection to deployment/config resolution.
3. **Q:** Who works the human-review queue for blocked PII-bearing documents — an internal ops role, or
   can any staffer handle it? — **why it matters:** decides whether the queue itself needs
   claims-based access scoping from day one, since it's a PII-adjacent surface — **my default if
   unanswered:** gate it behind claims like any other PII-adjacent surface — **what changes:** if it's
   a specific role, the queue's access model has to be designed in up front, not bolted on after.

## Where this could go wrong
- The egress tripwire only protects what actually passes through its chokepoint. If a future call site
  calls a provider's extraction method directly instead of going through the gated resolver, the
  structural guarantee is bypassed at that call site. The real fix for this is making the provider
  objects themselves unreachable except through the gated resolver (not exported/importable directly)
  — worth calling out as the single biggest unproven assumption in this plan.
- The gate is only as correct as the sensitivity classification feeding it. If a document is
  mislabeled `NON_PII` at ingestion, the gate does nothing wrong but the input was already wrong.
  Fail-closed default should extend here too: unknown or unset sensitivity is treated as `PII_BEARING`,
  never `NON_PII`, so a classification bug fails toward the safe side.
- This plan describes a type/shape change (an enum, a narrowed resolver signature) without writing the
  code — that's intentional for Round 1, which asks for the mechanism, not the implementation, but it
  means the plan is unverified until Step 2's build phase actually proves it compiles and holds under a
  real test.
