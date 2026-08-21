# Migrations

Alembic migrations create the per-domain schemas (`jobmanager`, `crewpay`, `warehouse`) and their
tables. The initial migration establishes: `jobmanager.customers`, `jobmanager.measure_docs`,
`crewpay.pay_events` (append-only), and `warehouse.pad_inventory`.

If your Round 2 fix changes the schema (e.g. a uniqueness constraint that makes a double-dispatch
structurally impossible), add a new revision here with an `upgrade()` **and** a `downgrade()`.
