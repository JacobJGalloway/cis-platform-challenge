"""Auth helpers.

Access is meant to be claims-based (Entra ID JWT), including per-user market-group scopes, enforced at
the query level. The ``User`` below is hydrated from the verified JWT; ``claims`` holds the raw token
claims, including ``market_scopes`` (the markets this user is entitled to).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Markets CIS currently operates in.
KNOWN_MARKETS = {"DFW", "OKC", "SHR", "TUL", "HOU"}

# Roles permitted to adjust warehouse inventory.
INVENTORY_ROLES = {"WAREHOUSE_ADMIN", "OPS"}


@dataclass
class User:
    user_id: str
    role: str
    claims: dict = field(default_factory=dict)  # includes {"market_scopes": ["DFW", ...]}


def can_adjust_inventory(user: User, market: str) -> bool:
    """Return True if ``user`` may adjust inventory in ``market``."""
    if user.role not in INVENTORY_ROLES:
        return False
    if market not in KNOWN_MARKETS:
        return False
    return True
