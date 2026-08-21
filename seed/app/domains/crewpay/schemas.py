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
    # None when status is "flagged_conflicting_amount" — no amount is resolved until a human
    # reviews the conflicting requests, so none is ever fabricated by picking one arbitrarily.
    amount_usd: float | None
    status: str  # "dispatched" | "already_dispatched" | "flagged_conflicting_amount"


class PayReviewFlag(BaseModel):
    """A conflict routed to a human for review instead of being auto-resolved."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_order_id: str
    pay_run_id: str
    reason: str
    conflicting_events: tuple[PayEvent, ...]
