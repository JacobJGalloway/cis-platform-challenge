# PLAN.md

> Commit this file **first**, on its own commit, before any other work. The timestamp is a signal.

## Problem in one paragraph
_Restate the problem in your own words — including the part you think is the actual trap._

## Architecture / mechanism
_How the safe path is structurally the easy path. Name the specific mechanism (interface capability,
sensitivity gate, egress tripwire, schema constraint), not the discipline. Draw the call graph if it
helps._

## Fail-closed behavior
_What the system does when the safe answer isn't available (no in-tenant provider for a hard doc; a
claim is missing; a value can't be verified). Who decides, and what is the default?_

## What I don't know yet
_The unknowns. Where you'd get "expected behavior" ground truth. Which signals you'd start from._

## Clarifying questions (3 sharp ones)
1. **Q:** … — **why it matters:** … — **my default if unanswered:** … — **what changes:** …
2. **Q:** … — **why it matters:** … — **my default if unanswered:** … — **what changes:** …
3. **Q:** … — **why it matters:** … — **my default if unanswered:** … — **what changes:** …

## Where this could go wrong
_The weak points of your own design. We trust a plan that names them over one that pretends there are
none._
