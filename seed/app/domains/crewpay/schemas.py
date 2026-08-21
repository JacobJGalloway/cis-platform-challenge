"""Crew Pay API schemas (Pydantic v2, frozen + extra=forbid)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PayEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str
    work_order_id: str
    pay_run_id: str
    crew_id: str
    event_type: str
    amount_usd: float
    labor_code: str
    occurred_at: str


class DispatchRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    work_order_id: str
    pay_run_id: str


class DispatchResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    work_order_id: str
    pay_run_id: str
    amount_usd: float
    status: str  # "dispatched" | "already_dispatched"
