# Synthetic fixtures (safe to publish)

All data here is invented. No real customer, crew, or THD data.

- **work_orders.csv** — roll quantities in YARDS; status color GREEN/GRAY/YELLOW per the legacy
  convention; markets DFW/OKC/SHR/TUL/HOU.
- **measure_docs.jsonl** — `pixel_text` simulates the PII printed on a field sheet (name, address,
  phone). `sensitivity` is `pii_bearing`. The `expected_extract` field is **scoring ground truth** for
  you to check your extraction against — it is *not* part of the `MeasureDoc` API schema (which is
  `frozen`/`extra="forbid"`), so strip it before POSTing.
- **crew_pay_events.jsonl** — append-only pay stream. Note the duplicate `pay.requested` for
  `WO-100841` (EVT-9001 and EVT-9003): an upstream retry. Your idempotency fix must make that safe.
