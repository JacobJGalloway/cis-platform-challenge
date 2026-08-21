# CLAUDE.md — CIS Platform Conventions (Hiring Challenge)

This is how we build. You don't have to love every line, but you should recognize *why* each exists —
and the seed code in [`seed/`](seed/) either honors these precepts or quietly breaks them. Noticing
which, and repairing it at the right layer, is the challenge.

We're going to spend most of this file on *how we think about a fix*, because that judgment — not
framework familiarity — is what this seat is. Read it once before you start; the examples below use
throwaway scenarios, **not** the ones in the seed, so they teach the reflex without doing your work
for you.

---

## Platform identity

- **Stack:** Python 3.12+ / FastAPI (backend), React 18 / Vite / TypeScript (frontend),
  PostgreSQL 16. Package manager `uv`. One Docker container per domain app.
- **API routes:** always under `/api/v1/{domain}`. Never expose raw DB IDs in URLs.
- **Models:** Pydantic v2 for API schemas (`frozen=True`, `extra="forbid"`); SQLAlchemy 2.0 for ORM.
- **Formatting/lint:** `ruff format` + `ruff check`, line length 99. Type hints on public functions and
  endpoints. Prefer async endpoints.
- **Errors:** structured `{"detail": "...", "code": "..."}`, never raw exceptions.

---

## The one idea underneath everything: structural over cultural

A **cultural** control depends on a human remembering, a reviewer catching, or a comment being obeyed.
A **structural** control makes the wrong state *impossible to construct* — the safe path is the path of
least resistance, and the unsafe path is something you'd have to actively fight the code to build.

Our litmus test for whether a fix is real:

> **Could an engineer who never read this file, six months from now, reconstruct the bad state by
> writing ordinary, reasonable-looking code?** If yes, you wrote a guard, not a fix.

A guard is an `if` someone can forget to add to the next code path. A fix changes the *shape* so the
next code path can't go wrong even if the author never heard of the rule.

### Worked example — guard vs. shape (throwaway scenario: request validation)

```python
# Cultural: validate downstream, trust every future caller to do the same.
async def handle_transfer(payload: dict) -> None:
    if "amount_cents" not in payload:          # a new caller next quarter forgets this
        raise ValueError("missing amount")
    ...

# Structural: a typed boundary that can't represent the bad input.
class TransferRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    amount_cents: int                          # missing -> rejected before your code runs
                                               # unexpected field -> rejected, can't smuggle through
```

The second version needs no discipline. The malformed request doesn't get *caught*; it can't *exist*
inside the system. That is the move we want, everywhere.

---

## The precepts

For each: the *smell* (what the cultural version looks like) and the *move* (the structural answer).
The examples are neutral — the seed's violations are yours to find.

### 1. Structural over cultural
Covered above. It's the lens for all the rest.

### 2. Fail-closed defaults
Absence of a permission, a claim, or a confident answer **denies**. Ambiguity around money or PII
routes to a human, never to an automatic action.

- **Smell:** `allow unless explicitly denied`; a default branch that proceeds; an empty/missing value
  treated as "fine."
- **Move:** deny unless something explicitly grants; on ambiguity, stop and flag.

```python
# Cultural (fails OPEN): everyone's allowed unless we remembered to block them.
def can_view(user, resource) -> bool:
    return resource.id not in user.denied_ids

# Structural (fails CLOSED): nothing is allowed unless a claim grants it; absence denies.
def can_view(user, resource) -> bool:
    return resource.scope in user.claims.get("scopes", ())
```

### 3. PII-free by construction on AI egress
Customer PII must not reach a provider that isn't in-tenant — guaranteed by the *shape* of the code
(a capability on the interface, a resolver that can't return an ineligible target for a sensitive
task, an egress tripwire), **not** by sanitizing we hope runs first. Manual scrubbing fails open.

- **Smell:** "we'll redact it before we send"; an `if target.is_safe:` bolted onto the call site; the
  guarantee living in a code-review rule.
- **Move:** make the sensitive payload *unable to reach* an ineligible target. Put the guarantee in
  resolution and in the type system, so a mis-wired future call fails closed instead of leaking.

```python
# Throwaway analogue — same reflex, applied to LOGGING (not the seed's egress path):

# Cultural: log the object, remember to redact PII later. (It's in the logs forever.)
logger.info("processed record", extra={"record": record.model_dump()})

# Structural: construct the log line from an allow-list projection. PII isn't in the record's
# *shape*, so it cannot appear in a log — no one has to remember anything.
logger.info("processed record", extra={"record_id": record.id, "market": record.market})
```

### 4. Claims, not roles
Access derives from JWT claims (Entra ID), including per-user market-group scopes, enforced at the
**query layer** — not from hardcoded role strings, not from a per-request DB lookup, not from a UI
check alone.

- **Smell:** `if user.role == "ADMIN"`; a constant list of markets/resources that gates entitlement;
  adding a market/store requires a code change.
- **Move:** derive the allowed set from the user's claims and intersect at the query. A new
  market/store added to reference data grants access to no one until it appears in someone's claims —
  it can't silently widen access.

### 5. Portability-first
Every external dependency sits behind an interface resolved by an env var. Services speak to
interfaces, not vendors. Dev uses simple/local backends; the platform stays deployable without any
single cloud vendor.

- **Smell:** a vendor SDK imported directly into domain logic; a provider chosen by a literal.
- **Move:** a thin interface with a portable fallback; the concrete backend chosen by configuration.

### 6. Domain boundaries
Each app owns one domain and shares nothing at the database level. **Customer records are owned by Job
Manager**; every other service references customers by ID and obtains display data through Job
Manager's API or a published event — never a cross-schema join or a foreign key into another domain's
tables.

- **Smell:** a query that names two domains' schemas; an FK across domains; importing another domain's
  models.
- **Move:** hold the foreign entity's ID only; fetch what you need via its owner's API/event; your
  query touches only your own schema. Degrade gracefully (show the ID) if the owner is unreachable.

### 7. One-write fan-out + append-only
State changes publish a single event; email and history are sinks on that one write. Money and
inventory operations are **idempotent** — replaying an event or retrying a request cannot double-apply.
Activity streams are append-only.

- **Smell:** a read-then-write with no uniqueness at the data layer; a side effect fired inline on
  every update and "protected" by an in-process check; a dedupe deferred to reporting.
- **Move:** a database constraint (or an idempotency key) makes the second application *rejected*, not
  merely unlikely; the duplicate is a successful no-op.

```python
# Throwaway analogue — idempotent NOTIFICATION (not the seed's money path):

# Cultural: send on every update; guard with a status check someone can forget on the next path.
async def on_update(order):
    if order.status != "cancelled":
        await send_email(order)                # a second update -> a second email

# Structural: the email is a sink on ONE published event, keyed by event_id. Replaying the event is
# a no-op because the sink has already recorded that event_id. Fanning out (email, history) hangs
# off that single write, so they can never disagree.
```

### 8. Propose, not act
AI surfaces structured suggestions for humans to approve. Auto-apply is earned per category only after
measured precision (≥95% vs. human approvals); low-confidence or compliance-flagged items require a
human indefinitely. No agent action commits a financial obligation or binds Cooper to a third party.
Every agent decision is logged immutably; any user can revert within 24h.

### 9. Defer with a named trigger
When something is genuinely risky or complex, defer it *explicitly* — documented rationale and a named
condition for when it ships. Don't silently skip it.

---

## Database
- One database, **per-domain schemas** (`jobmanager`, `crewpay`, `warehouse`, `identity`,
  `reference`). Audit tables live in a separate audit database.
- Alembic migrations; every migration has an upgrade **and** a downgrade.
- All tables carry `created_at` / `updated_at`, tz-aware, stored UTC (display `America/Chicago`).
- Prefer `is_active` soft-delete over hard delete for operational records. Index every FK column.

## Domain preservation (carried from the legacy FileMaker system)
- Roll quantities are in **YARDS**, not feet.
- Three-color status: **Green** = in stock, **Gray** = dispatched, **Yellow** = flagged for return.
- Label print happens **before** submit-to-database.
- Market filter selections are sticky across navigation.

---

## Working agreement for this challenge

- Branch from `main`. Branch name `fix/TICKET-ID-short-desc`. PR title includes `[TICKET-ID]`.
- **A fix without a test proving both the failure and the repair doesn't count.** For anything you
  touch, the test should fail on the code as delivered and pass on your change. Money/PII paths want an
  integration-style test against a realistic fixture, not just a unit test.
- **Read the surrounding code before you change it.** If you spot a precept violation *outside* your
  ticket, say so in your PR. Inheriting an opinionated system and noticing its rot is the job — not a
  bonus round, just what the work is.
- Write the **invariant** you restored into `DECISIONS.md`, in one sentence a future engineer inherits
  (e.g. *"X can never happen because the DB rejects it"*, not *"remember to check X"*).
- Keep the diff minimal and honest: no unrelated refactors, no committed `.env` or secrets, no
  lockfile churn you didn't intend, and don't squash your history before submitting — we read the
  timeline as part of understanding how you work.

We use AI here every day. Use it. We're interested in whether you can *direct* it toward the structural
answer — the litmus test at the top is the thing we're really reading.
