# T38 — Automatic Event Composer & Validator — Frozen Preparation Scope

**Preparation status:** PREPARED_GOVERNANCE_ONLY  
**Authoritative runtime status:** LOCKED
**Forward preparation baseline:** `havenline/QA-integration` @ `ac54e55fcf034673b97a1fcb02aba833a3ad2989`  

## Required outcome
- Compose LiveOps events only from pre-approved components and validate every generated schedule/reward/rule set before activation.
- Enforce deterministic schema validation, economy bounds, dependency checks, server-time windows, rollback metadata, and remote kill-switch compatibility.
- Reject malformed, conflicting, duplicate, expired, unsafe, or economically invalid events before player exposure.

## Explicit exclusions
No First Thaw authored content (T39), rotation calendar ownership (T40), or security foundation ownership (T41).

## Acceptance floor
LiveOps/economy/security/persistence gates mandatory; strict >9.0 unrounded.
