# CIS Platform — Staff Engineering Challenge

Welcome. This challenge is **plan-first** and **judgment-first**. We are *not* testing whether you
already know our stack (Python/FastAPI, React, PostgreSQL, Azure). We are testing **how you think**:
do you frame a problem and ask high-value questions before you build, and — the thing that actually
matters for this seat — do your *defaults* reach for the structural, fail-closed, PII-safe answer
rather than the convenient one?

> **Use AI tools. We expect and want it.** Claude Code, Cursor, Copilot — this is a Claude-Code shop.
> We evaluate how you *direct* AI, not whether you use it. A candidate who directs AI toward a
> structurally-sound design beats one who hand-writes a convenient-but-leaky one.

Read [`CLAUDE.md`](CLAUDE.md) before you start. It is how we build. You will not be quizzed on our
Laravel-free conventions, but **how we think about conventions is the whole point** — the seed
codebase either honors those precepts or quietly violates them, and noticing which is part of the test.

---

## Step 1 — Plan it (this IS the application, ~10 minutes)

The whole first step is ~10 minutes. A strong engineer lays the foundation in ten. Send us back
**two things**:

**A. A GitHub repo** (private is fine — add **`C0mputerBob`** as a collaborator) containing a
**`PLAN.md` committed *first*** (the git timestamp is part of the signal — commit it on its own,
before any other file). Your `PLAN.md` plans your answer to the **Round 1 problem** in
[`challenge/PROBLEM.md`](challenge/PROBLEM.md): *how you would run AI extraction over thousands of
measure documents — which contain customer PII baked into the image pixels — so that PII can never
reach a model outside our tenant boundary, and so that a future engineer cannot accidentally route
one to a provider that isn't in-tenant.* Design for the mistake you can't predict, not a checklist.
Say what you **don't know yet**: the unknowns, where you'd get "ground truth," which signals you'd
start from, and the questions you'd ask us — each with (a) why it matters, (b) your default if we
never answer, (c) what changes in your design depending on the answer. **3 sharp questions beat 15
shallow ones.**

**B. A short screen recording (≤5 min, 10 max — no face cam required)** of how you **START**: open
the problem in plan mode first (Claude Code's plan mode, your tool's planning step, or planning in
writing) and talk or caption your way through the plan above. We want to see you **frame before you
touch code** — that is the whole signal. Silent + captions, or just the `PLAN.md`, is fully
accepted; tell us which you chose. Keep secrets and personal tabs off screen. No judgment on accent,
delivery, or setup — only on whether you frame the problem before solving it.

You build nothing in Step 1. We judge **how you start** and **how you reason about an open-ended,
compliance-sensitive design problem** — the thing a strong engineer nails in ten minutes and a weak
one fakes.

### How to submit (2 links, that's it)
1. Your **GitHub repo** with `PLAN.md` committed first — add **`C0mputerBob`** as collaborator.
2. Your **screen-recording link** (Loom / YouTube-unlisted / Drive — ≤5 min).

Reply to our email with those two links. No cover letter, no forms. We reply to every complete
submission.

---

## Step 2 — Build it for real (only if your plan clears Step 1)

If your plan is strong, we hand you the **seed platform slice** in [`seed/`](seed/) — a runnable
FastAPI + PostgreSQL slice of three CIS domains (Job Manager, Crew Pay, Warehouse) carrying
**synthetic, masked data only**. Full spec: **[`challenge/ROUND2-PROBLEM.md`](challenge/ROUND2-PROBLEM.md)**.

Unlike Step 1, Step 2 **is** in our stack. The core of this role is production Python/FastAPI against
a relational PostgreSQL model, and we want to see you work there. You will pick **two** of the
[`tickets/`](tickets/), fix each **structurally** (not with a guard bolted on top), prove it with
tests, and write a one-page `DECISIONS.md` (our ADR-lite — template provided). The seed code compiles
and its smoke tests pass, but it contains **planted violations of our architectural precepts**. The
convenient fix makes a symptom go away; the correct fix makes the wrong thing *unconstructable*.

Most applications end at Step 1 — a sharp ten-minute plan is worth more to us than a polished
submission that never framed the problem.

---

## How we score

The short version, in priority order:

- **Structural over cultural (hard gate).** Did your fix make the wrong choice impossible to
  construct, or did you just guard against it and trust everyone to remember? A guard is not a fix.
- **Fail-closed (hard gate).** Defaults deny. On ambiguity — especially around money and PII — you
  flag for a human; you never auto-proceed.
- **PII-free by construction (hard gate).** No customer PII reaches a provider that isn't in-tenant.
  Structural, not "we remembered to scrub." Manual scrubbing fails open.
- **Domain boundaries.** You read another domain's data through its API or a published event, never a
  cross-schema join.
- **Generalization.** Your fix scales to cases you haven't seen. Hardcoding/enumerating = reject.
- **Documented reasoning.** `PLAN.md` and `DECISIONS.md` show *why*, including the calls you'd make
  differently. Sharp clarifying questions with why / default / what-changes.
- **Calibrated honesty.** We read your dead ends and unknowns as carefully as your wins. **Unproven
  claims score 0, and we reproduce a random sample — a claim that doesn't reproduce flags the whole
  submission.**

**Hard reject** regardless of code quality: PII can reach a non-in-tenant provider on any path you
touched; a money operation you touched can double-fire; you enforced access by hardcoded role instead
of claims; or you crossed a domain boundary with a direct DB read.
