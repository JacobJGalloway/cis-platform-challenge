"""Warehouse routes (/api/v1/warehouse)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.domains.warehouse.service import inventory_with_customer

router = APIRouter(prefix="/api/v1/warehouse", tags=["warehouse"])


@router.get("/inventory/{market}")
async def inventory(market: str, session: AsyncSession = Depends(get_session)) -> list[dict]:
    """List pad inventory for a market, with customer name for the pull sheet."""
    return await inventory_with_customer(session, market)
