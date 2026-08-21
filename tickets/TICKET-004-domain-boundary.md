# TICKET-004: Warehouse reads Job Manager's customer table directly

## Reported
The warehouse inventory view joins straight into `jobmanager.customers` to print the customer name.
Warehouse does not own customer records — Job Manager does — and this cross-schema join couples the
two domains at the database level.

## Where
- `app/domains/warehouse/service.py` — `inventory_with_customer()` runs a raw SQL
  `JOIN jobmanager.customers`.

## The precept
> **Domain boundaries.** Each app owns one domain and shares nothing at the DB level. Customer
> records are owned by Job Manager; other services reference customers by ID and fetch display data
> through Job Manager's API or a published event — never a cross-schema join or a foreign key into
> another domain's tables.

## What we are NOT looking for
Moving the join into a view, or adding a foreign key to `jobmanager.customers`. Both still couple the
domains.

## What a structural fix looks like
- Warehouse holds only the `customer_id` (an opaque reference). Display data (the name) is obtained
  through **Job Manager's API** or from a **published event** Job Manager emits — the warehouse query
  touches only `warehouse.*`.
- Show how you'd keep it decoupled and resilient (e.g. the view degrades to showing the ID if Job
  Manager is unavailable, rather than failing the whole page — fail-closed, but usefully).

## Definition of done
- The warehouse inventory query references only the `warehouse` schema; a test asserts no
  cross-schema access in that path.
- A test proving the inventory view still returns rows with a customer reference (via the seam you
  chose), including the degraded path.
- `DECISIONS.md` entry naming the invariant.
