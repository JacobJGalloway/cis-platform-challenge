"""Model router: resolves an AI provider for a task.

Providers are registered here and selected by capability. The public provider is preferred when it can
do the job because it is cheaper and handles handwriting better; the in-tenant provider is the
fallback.
"""

from __future__ import annotations

from app.ai.providers.base import AIProvider
from app.ai.providers.mock_doc_intelligence import MockDocIntelligenceProvider
from app.ai.providers.public_vision import PublicVisionProvider

# Registered providers, in preference order (cheapest/most-capable first).
_REGISTRY: list[AIProvider] = [
    PublicVisionProvider(),
    MockDocIntelligenceProvider(),
]


def resolve_provider(capability: str) -> AIProvider:
    """Return the first registered provider that offers ``capability``.

    Args:
        capability: e.g. "doc_extract".
    """
    for provider in _REGISTRY:
        if capability in provider.capabilities:
            return provider
    raise LookupError(f"No provider offers capability {capability!r}")
