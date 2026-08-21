"""Model router: resolves an AI provider for a task.

Providers are registered here and selected by capability. Task sensitivity is an input to
resolution: a task carrying customer PII (``pii_bearing=True``) can only resolve to a provider that
runs inside the CIS tenant boundary (``in_tenant is True``). Non-in-tenant providers are excluded
from the eligible set for sensitive tasks before a candidate is ever picked — a leak isn't caught
after the fact, it can't be constructed.
"""

from __future__ import annotations

from app.ai.providers.base import AIProvider
from app.ai.providers.mock_doc_intelligence import MockDocIntelligenceProvider
from app.ai.providers.public_vision import PublicVisionProvider

# Registered providers, in preference order (cheapest/most-capable first among ELIGIBLE providers).
_REGISTRY: list[AIProvider] = [
    PublicVisionProvider(),
    MockDocIntelligenceProvider(),
]


class NoEligibleProviderError(Exception):
    """Raised when no registered provider is both capable and eligible for a task.

    For a ``pii_bearing`` task this means no in-tenant provider offers the capability. Callers must
    treat this as fail-closed: flag for human review / in-tenant fallback, never fall back to a
    provider outside the eligible set.
    """


class PiiLeakError(Exception):
    """Raised at the egress point if a pii_bearing payload is about to reach a non-in-tenant
    provider. Defense in depth: ``resolve_provider`` should already make this unreachable, but a
    future call path that resolves a provider some other way still fails closed here instead of
    sending bytes.
    """


def resolve_provider(capability: str, *, pii_bearing: bool) -> AIProvider:
    """Return the preferred eligible provider that offers ``capability``.

    Args:
        capability: e.g. "doc_extract".
        pii_bearing: True if the task's payload may contain customer PII. When True, only
            providers with ``in_tenant is True`` are eligible — non-in-tenant providers are
            excluded from consideration entirely, not merely deprioritized.

    Raises:
        NoEligibleProviderError: no eligible provider offers this capability. For a pii_bearing
            task, the caller must fail closed (flag for human / in-tenant fallback) rather than
            retry against an ineligible provider.
    """
    eligible = [
        provider
        for provider in _REGISTRY
        if capability in provider.capabilities and (provider.in_tenant or not pii_bearing)
    ]
    if not eligible:
        raise NoEligibleProviderError(
            f"No eligible provider offers {capability!r} (pii_bearing={pii_bearing})"
        )
    return eligible[0]
