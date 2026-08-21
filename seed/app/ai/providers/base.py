"""AI provider interface.

Every provider is resolved behind this interface (portability-first). A provider declares whether it
runs inside the CIS Azure tenant boundary via ``in_tenant``. Note: ``in_tenant`` is a stronger claim
than "no-training" or "subscription-isolated" — it means customer bytes never leave the tenant.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AIProvider(Protocol):
    name: str
    # True only if the provider runs inside the CIS Azure tenant boundary.
    in_tenant: bool
    # Coarse capability tags the router matches against (e.g. "doc_extract", "vision").
    capabilities: frozenset[str]

    async def extract(self, content: bytes, prompt: str) -> dict:
        """Run extraction over raw document content and return structured fields."""
        ...
