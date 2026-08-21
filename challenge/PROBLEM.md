# Round 1 — Keep customer PII inside the tenant boundary (plan-first, ~10 min)

This is a **planning** problem. You write no solution code. You commit a `PLAN.md` (first) and record
a short "how I start" video. Use any language, any AI tool — we care how you *direct* the tool and how
you frame the problem.

> This is **Step 1 of 2**. The build (Step 2) is released only if your plan clears. Do this well.

## Context

CIS installs flooring for The Home Depot. Every job has **measure documents** — PDFs and phone photos
of a measure tech's field sheet. We want AI to read them: extract room dimensions, product, square
footage, special conditions. Thousands of documents, growing daily.

The catch: **these documents contain customer PII baked into the image pixels** — the homeowner's
name, street address, and phone number are printed on the sheet. You cannot reliably strip PII from a
rasterized field photo before extraction; the text you want and the PII you must protect are the same
pixels. There is no "sanitize step" that provably runs first and provably works.

We run multiple AI providers behind one interface. Some run **inside our Azure tenant boundary**
(Azure AI Document Intelligence, Azure OpenAI). Some do not. A model that is merely "no-training" or
"subscription-isolated" is **not** the same as in-tenant — human review of flagged content can still
occur outside our boundary under default abuse monitoring.

## The problem

Plan how you would run AI extraction over these documents such that:

1. **Customer PII never reaches a provider that is not in-tenant** — on any code path, including
   fallbacks, retries, error handlers, and future features written by an engineer who never read this
   README.
2. **A future engineer cannot accidentally undo it.** The safe path must be the path of least
   resistance; the leaky path must be something they'd have to work to construct.
3. It **degrades sensibly** when the only capable provider for a task is not in-tenant (fail-closed:
   what happens then?).

## What a strong plan does

- Names the **structural** mechanism, not the disciplinary one. "We'll scrub PII first" is the wrong
  answer here (the pixels are the PII, and scrubbing fails open). We're looking for something like:
  a **capability model on the provider interface** (an `in_tenant` flag), a **task-sensitivity gate**
  that makes a `pii_bearing` task *unable to resolve* to a non-in-tenant provider, an **egress
  tripwire** that raises before bytes leave, and **schemas that forbid** smuggling raw content into a
  provider call. Make the leak unconstructable.
- Distinguishes the **boundary** question (in-tenant vs. not) from the weaker **data-handling**
  guarantees (no-training, isolation) and explains why the weaker ones don't satisfy the constraint.
- Says what happens on the **fail-closed** path — when the best model for a hard document is not
  in-tenant, what does the system do, and who decides?
- Lists the **unknowns** and **3 sharp clarifying questions**, each with: why it matters, your default
  if we never answer, what changes in your design depending on the answer.

## What a weak plan does (any one of these is a hard flag)

- Relies on remembering to sanitize, redact, or "be careful."
- Treats no-training / data-isolation as equivalent to in-tenant.
- Puts the guarantee in a code-review rule or a comment instead of the type system / call graph.
- Has no fail-closed story — silently falls back to whatever provider is available.

## Deliverables

1. `PLAN.md` committed **first**, on its own commit (template: [`PLAN.template.md`](PLAN.template.md)).
2. A ≤5-minute "how I start" recording (or silent + captions, or a written walkthrough — your choice).

We reproduce nothing in Round 1 — this is pure design judgment. Say what you don't know. A plan that
names its own weak points beats one that pretends there are none.
