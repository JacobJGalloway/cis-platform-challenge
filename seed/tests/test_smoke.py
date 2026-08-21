"""Smoke tests. These pass on the seed as delivered.

They intentionally do NOT test the planted precept violations — writing the test that exposes each
violation is part of Round 2. See tickets/.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.anyio
async def test_measure_doc_review_returns_rooms():
    from app.domains.jobmanager.ai_review import review_measure_doc
    from app.domains.jobmanager.schemas import MeasureDoc

    doc = MeasureDoc(
        doc_id="MD-TEST",
        work_order_id="WO-1",
        market="DFW",
        source="pdf",
        sensitivity="pii_bearing",
        pixel_text="MEASURE SHEET Customer: Test Person living 10x10",
    )
    result = await review_measure_doc(doc)
    assert result.doc_id == "MD-TEST"
    assert "living" in result.rooms
