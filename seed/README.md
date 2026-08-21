# CIS Seed Slice

A runnable FastAPI + PostgreSQL slice of three CIS domains — **Job Manager**, **Crew Pay**,
**Warehouse** — carrying synthetic data only. It compiles and its smoke tests pass. It also contains
four planted violations of the CIS precepts in [`../CLAUDE.md`](../CLAUDE.md); see [`../tickets/`](../tickets/).

## Run

```bash
cp .env.example .env
uv sync
docker compose up -d db
uv run alembic upgrade head        # creates per-domain schemas + tables
uv run python -m app.seed_data     # loads synthetic crew-pay stream
uv run uvicorn app.main:app --reload
uv run pytest -q
```

## Layout
- `app/ai/` — provider interface (`in_tenant` capability) + model router
- `app/domains/jobmanager/` — measure-doc AI review
- `app/domains/crewpay/` — installer pay events (append-only stream)
- `app/domains/warehouse/` — pad inventory
- `app/auth.py` — market-scope access checks
