"""initial schemas + tables

Revision ID: 0001_initial
Create Date: 2026-07-28
"""

from __future__ import annotations

revision = "0001_initial"
down_revision = None


def upgrade() -> None:
    # Pseudocode outline — the real revision uses op.create_table with per-schema tables:
    #   CREATE SCHEMA jobmanager; CREATE SCHEMA crewpay; CREATE SCHEMA warehouse;
    #   jobmanager.customers(customer_id PK, customer_name, market, created_at, updated_at)
    #   jobmanager.measure_docs(doc_id PK, work_order_id, market, sensitivity, ...)
    #   crewpay.pay_events(event_id PK, work_order_id, pay_run_id, event_type, amount_usd, ...)
    #   warehouse.pad_inventory(work_order_id PK, market, customer_id, roll_qty_yards, status_color)
    # NOTE: crewpay.pay_events has NO uniqueness guard on (work_order_id, pay_run_id, event_type)
    #       for dispatched events. That omission is deliberate — see TICKET-002.
    ...


def downgrade() -> None:
    ...
