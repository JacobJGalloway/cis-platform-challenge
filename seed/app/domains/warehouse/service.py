"""Warehouse service (Pad Inventory domain).

Warehouse owns pad inventory. It does NOT own customer records — those belong to Job Manager. A
warehouse view sometimes needs the customer name (e.g. to print on a pull sheet).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def inventory_with_customer(session: AsyncSession, market: str) -> list[dict]:
    """Return pad inventory rows for a market, enriched with the customer name.

    Roll quantities are in YARDS. Status color: GREEN=in stock, GRAY=dispatched, YELLOW=flagged
    for return.
    """
    # Join warehouse pad inventory to the customer record to get the display name in one query.
    sql = text(
        """
        SELECT p.work_order_id,
               p.roll_qty_yards,
               p.status_color,
               c.customer_name
        FROM warehouse.pad_inventory p
        JOIN jobmanager.customers c ON c.customer_id = p.customer_id
        WHERE p.market = :market
        ORDER BY p.work_order_id
        """
    )
    rows = (await session.execute(sql, {"market": market})).mappings().all()
    return [dict(r) for r in rows]
