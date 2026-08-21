"""Job Manager routes (/api/v1/jobmanager)."""

from __future__ import annotations

from fastapi import APIRouter

from app.domains.jobmanager.ai_review import review_measure_doc
from app.domains.jobmanager.schemas import MeasureDoc, ReviewResult

router = APIRouter(prefix="/api/v1/jobmanager", tags=["jobmanager"])


@router.post("/measure-docs/review", response_model=ReviewResult)
async def review(doc: MeasureDoc) -> ReviewResult:
    """Run AI extraction over a measure document and return the structured result."""
    return await review_measure_doc(doc)
