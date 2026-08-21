"""Public multi-modal vision provider (NOT in-tenant).

High accuracy and cheap, but runs outside the CIS tenant boundary. Under default abuse monitoring,
flagged content may be reviewed by humans outside our boundary. Fine for non-PII tasks; must never
receive pii_bearing content.
"""

from __future__ import annotations

import re


class PublicVisionProvider:
    name = "public-vision-xl"
    in_tenant = False
    capabilities = frozenset({"doc_extract", "vision", "handwriting"})

    async def extract(self, content: bytes, prompt: str) -> dict:
        text = content.decode("utf-8", errors="ignore")
        rooms = re.findall(r"\b(master_br|hall|living|stairs|kitchen|bonus)\b", text.lower())
        return {"provider": self.name, "rooms": sorted(set(rooms)), "raw_len": len(text)}
