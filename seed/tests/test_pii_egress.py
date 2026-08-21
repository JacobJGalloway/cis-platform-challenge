"""TICKET-001: a pii_bearing measure doc must never reach a non-in-tenant AI provider.

These are integration-style tests against `review_measure_doc`, the real call path a measure doc
takes, not a unit test of `resolve_provider` in isolation — the leak is only real once bytes move.
"""

from __future__ import annotations

import pytest

from app.ai import router as ai_router
from app.ai.router import NoEligibleProviderError, PiiLeakError, resolve_provider
from app.domains.jobmanager.ai_review import review_measure_doc
from app.domains.jobmanager.schemas import MeasureDoc


def _doc(sensitivity: str, doc_id: str = "MD-TEST") -> MeasureDoc:
    return MeasureDoc(
        doc_id=doc_id,
        work_order_id="WO-1",
        market="DFW",
        source="pdf",
        sensitivity=sensitivity,
        pixel_text="MEASURE SHEET Customer: Test Person 123 Any St living 10x10",
    )


@pytest.mark.anyio
async def test_pii_bearing_doc_never_reaches_non_in_tenant_provider():
    """On the original router, PublicVisionProvider (in_tenant=False) is first in preference order
    and gets picked regardless of sensitivity — this fails on that code and passes on the fix,
    which excludes non-in-tenant providers from the eligible set for pii_bearing tasks.
    """
    result = await review_measure_doc(_doc("pii_bearing"))
    assert result.provider != "public-vision-xl"
    assert result.provider == "azure-doc-intelligence"


@pytest.mark.anyio
async def test_non_pii_doc_can_still_use_public_provider():
    """We didn't over-rotate: a non_pii task is still free to use the cheaper public provider."""
    result = await review_measure_doc(_doc("non_pii"))
    assert result.provider == "public-vision-xl"


def test_resolve_provider_excludes_non_in_tenant_for_pii_bearing():
    provider = resolve_provider("doc_extract", pii_bearing=True)
    assert provider.in_tenant is True


def test_resolve_provider_prefers_public_for_non_pii():
    provider = resolve_provider("doc_extract", pii_bearing=False)
    assert provider.in_tenant is False


@pytest.mark.anyio
async def test_no_in_tenant_provider_flags_for_human_review_instead_of_leaking(monkeypatch):
    """Fail-closed, generalized: if no in-tenant provider is registered for the capability at all,
    a pii_bearing doc must be flagged for human review, never routed to the public provider.
    """
    monkeypatch.setattr(ai_router, "_REGISTRY", [])

    result = await review_measure_doc(_doc("pii_bearing", doc_id="MD-NOPROVIDER"))
    assert result.requires_human_review is True
    assert result.provider == "none"
    assert result.rooms == []


def test_no_eligible_provider_raises_when_registry_empty():
    ai_router._REGISTRY, saved = [], ai_router._REGISTRY
    try:
        with pytest.raises(NoEligibleProviderError):
            resolve_provider("doc_extract", pii_bearing=True)
    finally:
        ai_router._REGISTRY = saved


@pytest.mark.anyio
async def test_egress_tripwire_blocks_mis_wired_call(monkeypatch):
    """Defense in depth: even if a future call path bypasses resolve_provider's filtering and hands
    review_measure_doc a non-in-tenant provider directly for a pii_bearing doc, the tripwire in
    ai_review raises rather than sending content.
    """
    from app.ai.providers.public_vision import PublicVisionProvider
    from app.domains.jobmanager import ai_review as ai_review_module

    monkeypatch.setattr(
        ai_review_module,
        "resolve_provider",
        lambda capability, *, pii_bearing: PublicVisionProvider(),
    )

    with pytest.raises(PiiLeakError):
        await review_measure_doc(_doc("pii_bearing", doc_id="MD-MISWIRED"))
