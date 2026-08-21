# Round 2 — Build it structurally (in-stack, released only after Step 1 clears)

You now have the **seed slice** in [`../seed/`](../seed/): a runnable FastAPI + PostgreSQL slice of
three CIS domains — **Job Manager** (measure docs + AI review), **Crew Pay** (installer pay events),
and **Warehouse** (pad inventory) — carrying **synthetic, masked data only** (`../challenge/data/`).

The seed compiles and `pytest` smoke tests pass. It also **violates our precepts in four specific
places**, each captured as a ticket in [`../tickets/`](../tickets/). Every violation is a real one we
have seen made on real platforms — the convenient code that makes a symptom disappear versus the
structural code that makes the wrong thing impossible to build.

## Your task

1. **Pick two tickets.** Do them well rather than four half-way.
2. **Fix each one structurally.** Not a guard bolted on top of the convenient code — a change to the
   *shape* of the code so the violation cannot be reconstructed. If your fix is "add an `if` that
   checks the thing," ask whether a stronger candidate would have made the check unnecessary.
3. **Prove it with tests.** For each fix, a test that *fails on the original code* and *passes on
   yours*, plus a test that proves the legitimate path still works. Compliance-sensitive code (PII
   egress, pay) needs an integration-style test against a realistic fixture, not just a unit test.
4. **Write `DECISIONS.md`** (ADR-lite, template in [`DECISIONS.template.md`](DECISIONS.template.md)) —
   one short entry per fix: the violation, the two options (convenient vs. structural), which you
   chose and why, and the **invariant** you restored in one inheritable sentence.
5. **Big-picture pass.** In your PR description, note any of the *other two* planted violations you
   spotted but didn't fix. Noticing rot outside your lane is the job.

## Rules

- **In our stack.** FastAPI + PostgreSQL + Pydantic v2 + SQLAlchemy 2.0, per `../CLAUDE.md`. If your
  fix needs a schema change, write the Alembic migration with an upgrade **and** a downgrade.
- **No hardcoding to the fixture.** Your fix must generalize to markets, work orders, and documents
  you have never seen. Enumerating the seed rows to pass = reject.
- **Fail-closed.** Where you touch money or PII, the safe default on ambiguity is "stop and flag a
  human," never "proceed."
- **Keep the diff honest.** Minimal files, no unrelated refactors, no committed `.env` or secrets, no
  squashing your commit history before you submit — we read the timeline.
- **Use AI freely.** Direct it toward the structural answer. We can tell the difference between a
  candidate who used a model to build the right thing and one who let the model build the convenient
  thing.

## Run it

```bash
cd seed
cp .env.example .env
uv sync
docker compose up -d db          # PostgreSQL 16
uv run alembic upgrade head      # create schemas + tables
uv run python -m app.seed_data   # load synthetic fixtures
uv run uvicorn app.main:app --reload
# in another shell:
uv run pytest -q
```

## Submit

Your repo, `PLAN.md` (Round 1) still committed first, then your two fixes + their tests +
`DECISIONS.md`, on a branch per ticket, PRs targeting `main`. Add **`C0mputerBob`** as collaborator.
The auto-reviewer will comment on each PR; a human reads everything scored ≥ 8.
