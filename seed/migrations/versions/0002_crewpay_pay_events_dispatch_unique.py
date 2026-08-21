"""crewpay.pay_events table + uniqueness guard on dispatched events

0001_initial left crewpay.pay_events as a pseudocode outline and never actually created it — this
revision provides the first real DDL for the table, and includes the uniqueness guard from the
start so the omission called out in 0001's comment (TICKET-002) can't be reintroduced by some
future "let's finish the outline" migration that copies the shape without the guard.

A work order can only ever have one pay.dispatched event per pay run: a second attempt to dispatch
(retry, race, replay) is rejected by the database itself via a partial unique index, not by an
application-level check-then-write.

Revision ID: 0002_crewpay_pay_events_dispatch_unique
Create Date: 2026-08-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_crewpay_pay_events_dispatch_unique"
down_revision = "0001_initial"


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS crewpay")

    op.create_table(
        "pay_events",
        sa.Column("event_id", sa.String, primary_key=True),
        sa.Column("work_order_id", sa.String, nullable=False),
        sa.Column("pay_run_id", sa.String, nullable=False),
        sa.Column("crew_id", sa.String, nullable=False),
        sa.Column("event_type", sa.String, nullable=False),
        sa.Column("amount_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("labor_code", sa.String, nullable=False),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema="crewpay",
    )
    op.create_index("ix_pay_events_work_order_id", "pay_events", ["work_order_id"], schema="crewpay")

    # A work order + pay run can have at most one dispatched event. This is the invariant restored
    # by TICKET-002: the second write for the same key is rejected here, not merely detected.
    op.create_index(
        "uq_pay_events_dispatched_per_work_order_pay_run",
        "pay_events",
        ["work_order_id", "pay_run_id"],
        unique=True,
        schema="crewpay",
        postgresql_where=sa.text("event_type = 'pay.dispatched'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_pay_events_dispatched_per_work_order_pay_run", table_name="pay_events", schema="crewpay"
    )
    op.drop_index("ix_pay_events_work_order_id", table_name="pay_events", schema="crewpay")
    op.drop_table("pay_events", schema="crewpay")
