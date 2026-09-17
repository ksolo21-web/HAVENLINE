# T13 — Progressive Difficulty & spend-blind Challenge Director — Frozen Preparation Scope

**Preparation status:** PREPARED_GOVERNANCE_ONLY  
**Authoritative runtime status:** LOCKED  
**Forward preparation baseline:** `havenline/QA-integration` @ `ac54e55fcf034673b97a1fcb02aba833a3ad2989`  

## Required outcome
- Implement deterministic progressive difficulty driven by approved Level 1–100 progression state and gameplay-performance signals.
- Normal-player difficulty is spend-blind: purchase history, premium balance, VIP, store activity, and spend-derived signals are forbidden inputs.
- Preserve the explicit owner-only GM_CHALLENGE policy path, isolated from normal-player fairness/analytics.
- Provide bounded escalation, recovery/de-escalation, anti-spike rules, deterministic replay tests, and readable feedback.

## Explicit exclusions
- No billing, store, entitlement, VIP implementation, LiveOps scheduling, telemetry backend, or T21 hostiles/weapon progression.
- No runtime activation until T12 is APPROVED and integrated.

## Acceptance floor
Universal G1–G14 gates apply where relevant; every mandatory reviewed dimension must be strictly >9.0 unrounded, target 10/10, with zero unresolved mandatory defects and exact-source evidence.

## Non-disruption
Preparation owns no active runtime path yet, changes no upstream task state, does not self-approve production, and cannot integrate itself.
