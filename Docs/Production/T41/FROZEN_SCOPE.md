# T41 — Anti-cheat and economic-security foundation — Frozen Preparation Scope

**Preparation status:** PREPARED_GOVERNANCE_ONLY  
**Authoritative runtime status:** LOCKED

## Required outcome
- Establish fail-closed authority boundaries for economy, purchases, VIP, LiveOps, privileged operations, replay/idempotency, tamper detection, and competitive-value isolation.
- Never trust client save/local state, clock, premium balance, receipt claims, VIP flags, or remote config as authority for privileged/economic mutations.
- Protect Game Master role resolution and privileged commands with server authorization, audit, replay/tamper defenses, and noncompetitive marking for admin mutations.

## Explicit exclusions
No T43 identity binding implementation and no T66 final attack review.

## Acceptance floor
C9 security is mandatory; deterministic adversarial tests and exact-source evidence required; strict >9.0 unrounded.
