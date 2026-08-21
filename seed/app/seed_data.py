"""Load synthetic fixtures into memory (crew pay) and print a summary.

Real seed loads Postgres via Alembic-created schemas; here we hydrate the crewpay in-memory stream so
the smoke tests and manual pokes work without a DB. All data is synthetic.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.domains.crewpay.schemas import PayEvent
from app.domains.crewpay.service import load_events

DATA = Path(__file__).resolve().parents[2] / "challenge" / "data"


def load_pay_events() -> list[PayEvent]:
    events = [PayEvent(**json.loads(line)) for line in (DATA / "crew_pay_events.jsonl").read_text().splitlines() if line.strip()]
    load_events(events)
    return events


if __name__ == "__main__":
    evs = load_pay_events()
    print(f"Loaded {len(evs)} pay events from {DATA/'crew_pay_events.jsonl'}")
