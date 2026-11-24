# T34 — Server-authoritative premium economy — Frozen Preparation Scope

**Preparation status:** PREPARED_GOVERNANCE_ONLY  
**Authoritative runtime status:** LOCKED
**Forward preparation baseline:** `havenline/QA-integration` @ `ac54e55fcf034673b97a1fcb02aba833a3ad2989`  

## Required outcome
- Define a server-authoritative premium-currency/entitlement boundary; the client may request/display but must not authoritatively mint, debit, credit, or grant premium value.
- Preserve normal-player economy/fairness and idempotent transaction semantics.
- Game Master zero-cost grants must be server-authoritative, idempotent, audited, revenue-excluded, and must not alter normal-player pricing.

## Explicit exclusions
No storefront purchase UX/billing implementation (T35) and no VIP implementation (T36).

## Acceptance floor
Security/economy/persistence evidence is mandatory; strict >9.0 unrounded per applicable dimension.
