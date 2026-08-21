# TICKET-001: Measure-doc review can send customer PII to a non-in-tenant provider

## Reported
A `pii_bearing` measure document (homeowner name/address/phone printed on the sheet) can be sent to
an AI provider that runs **outside** the CIS tenant boundary. Extraction "works," so nothing looks
wrong — but customer PII is leaving the tenant.

## Where
- `app/ai/router.py` — `resolve_provider()` selects by capability/cost only. It has no knowledge of
  the task's sensitivity, and the public (not in-tenant) provider is first in preference order.
- `app/domains/jobmanager/ai_review.py` — hands the raw `pixel_text` (the PII) to whatever provider
  the router returns.

## The precept
> **PII-free by construction on AI egress.** Customer PII must not reach a provider whose
> `in_tenant` is false — guaranteed by the shape of the code, not by remembering to scrub. Manual
> scrubbing fails open (the pixels *are* the PII).

## What we are NOT looking for
A scrub/redact step before the call, or an `if provider.in_tenant:` check bolted into `ai_review`.
Those are guards a future feature will forget.

## What a structural fix looks like (design it yourself; this is the shape)
- The router **cannot resolve** a `pii_bearing` task to a provider whose `in_tenant` is false — the
  sensitivity is an input to resolution, and non-in-tenant providers are excluded from the eligible
  set for sensitive tasks. A leak isn't caught; it's unrepresentable.
- An **egress tripwire** raises (e.g. `PiiLeakError`) before bytes are handed to a non-in-tenant
  provider, so even a mis-wired future call path fails closed rather than leaking.
- **Fail-closed:** if no in-tenant provider can do the task, the document is flagged for a human /
  in-tenant fallback — never silently routed to the public provider.

## Definition of done
- A test that **fails on the current code** by proving a `pii_bearing` doc reaches a non-in-tenant
  provider, and **passes on your fix**.
- A test proving a `non_pii` task can still use the public provider (you didn't over-rotate).
- `DECISIONS.md` entry naming the invariant, e.g. *"A pii_bearing task can never resolve to a
  provider whose in_tenant is false."*
