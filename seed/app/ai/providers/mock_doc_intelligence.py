"""In-tenant document-extraction provider (stands in for Azure AI Document Intelligence).

Runs inside the CIS tenant boundary: safe for pii_bearing content.
"""

from __future__ import annotations

import re


class MockDocIntelligenceProvider:
    name = "azure-doc-intelligence"
    in_tenant = True
    capabilities = frozenset({"doc_extract", "vision"})

    async def extract(self, content: bytes, prompt: str) -> dict:
        text = content.decode("utf-8", errors="ignore")
        # Trivial deterministic "extraction" for the fixture; a real impl calls the Azure resource.
        rooms = re.findall(r"\b(master_br|hall|living|stairs|kitchen|bonus)\b", text.lower())
        return {"provider": self.name, "rooms": sorted(set(rooms)), "raw_len": len(text)}
