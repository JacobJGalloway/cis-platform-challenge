"""Crew Pay routes (/api/v1/crewpay)."""

from __future__ import annotations

from fastapi import APIRouter

from app.domains.crewpay.schemas import DispatchRequest, DispatchResult
from app.domains.crewpay.service import dispatch_pay

router = APIRouter(prefix="/api/v1/crewpay", tags=["crewpay"])


@router.post("/dispatch", response_model=DispatchResult)
async def dispatch(req: DispatchRequest) -> DispatchResult:
    """Dispatch pay for a work order + pay run."""
    return await dispatch_pay(req.work_order_id, req.pay_run_id)
