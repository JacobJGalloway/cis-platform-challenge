"""Job Manager API schemas (Pydantic v2, frozen + extra=forbid per CIS convention)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MeasureDoc(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    doc_id: str
    work_order_id: str
    market: str
    source: str
    sensitivity: str  # "pii_bearing" | "non_pii"
    pixel_text: str   # the field-sheet content (may contain PII printed on the page)


class ReviewResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    doc_id: str
    provider: str
    rooms: list[str]
    requires_human_review: bool
