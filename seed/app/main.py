"""CIS platform seed slice — FastAPI entrypoint.

Mounts three domains behind /api/v1. Each domain owns its data; cross-domain access is meant to go
through APIs/events, never shared DB access.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.domains.crewpay.router import router as crewpay_router
from app.domains.jobmanager.router import router as jobmanager_router
from app.domains.warehouse.router import router as warehouse_router

app = FastAPI(title="CIS Platform — Hiring Challenge Seed", version="0.1.0")

app.include_router(jobmanager_router)
app.include_router(crewpay_router)
app.include_router(warehouse_router)


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
