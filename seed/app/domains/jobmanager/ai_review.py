"""AI review of measure documents (Job Manager domain).

Measure documents are photos/PDFs of a measure tech's field sheet. We extract rooms, product, and
square footage. The document's ``sensitivity`` is carried on the record; ``pii_bearing`` documents
have the homeowner's name, address, and phone printed in the image.
"""

from __future__ import annotations

from app.ai.router import resolve_provider
from app.domains.jobmanager.schemas import MeasureDoc, ReviewResult


async def review_measure_doc(doc: MeasureDoc) -> ReviewResult:
    """Extract structured fields from a measure document.

    The document content is the field sheet image bytes. We hand it to an extraction provider and
    return the structured result plus which provider ran.
    """
    provider = resolve_provider("doc_extract")

    # The pixel content IS the document — including any PII printed on the sheet.
    content = doc.pixel_text.encode("utf-8")
    extracted = await provider.extract(content, prompt="Extract rooms, product, and total square feet.")

    return ReviewResult(
        doc_id=doc.doc_id,
        provider=extracted["provider"],
        rooms=extracted.get("rooms", []),
        requires_human_review=False,
    )
