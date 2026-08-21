# TICKET-003: Inventory access is by hardcoded role, not the user's market claims

## Reported
A warehouse admin scoped to DFW can adjust **OKC** inventory. Access is granted by role, not by the
markets the user is actually entitled to, and adding a new market means editing a code constant.

## Where
- `app/auth.py` — `can_adjust_inventory(user, market)` checks `user.role in INVENTORY_ROLES` and
  `market in KNOWN_MARKETS`, but never consults the user's own `claims["market_scopes"]`. Any
  inventory role can touch any known market.

## The precept
> **Claims, not roles.** Access derives from JWT claims — including per-user market-group scopes —
> enforced at the query level. Adding a market must not be able to grant cross-market access by
> accident. Absence of a claim denies (fail-closed).

## What we are NOT looking for
Adding OKC-vs-DFW special cases, or a second hardcoded map of role→markets. The rule must come from
the user's claims and generalize to markets that don't exist yet.

## What a structural fix looks like
- Allowed markets are derived from `user.claims["market_scopes"]`; the check is
  `market in user.market_scopes` (plus the role gate). No hardcoded market list gates entitlement.
- **Fail-closed:** a missing/empty `market_scopes` claim denies. A new market added to reference data
  grants access to no one until it appears in someone's claims — it cannot silently widen access.
- Consider where this is enforced: a UI check alone is not enough; scoping belongs at the query/data
  layer.

## Definition of done
- A test that **fails on the current code**: a DFW-scoped admin is allowed to adjust OKC, and
  **passes on your fix** (denied).
- A test proving a DFW-scoped admin can still adjust DFW, and that a missing claim denies.
- `DECISIONS.md` entry naming the invariant.
