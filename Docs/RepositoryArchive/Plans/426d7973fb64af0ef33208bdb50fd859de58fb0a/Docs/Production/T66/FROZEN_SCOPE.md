# T66 — Security/exploit attack review — Frozen Preparation Scope

**Preparation status:** PREPARED_GOVERNANCE_ONLY  
**Authoritative runtime status:** LOCKED

## Required outcome
- Attack the completed security/economy/identity/LiveOps boundaries rather than merely confirming happy paths.
- Cover role escalation, forged local/save/email state, receipt fraud, request replay, idempotency abuse, premium/VIP tampering, clock/time manipulation, cloud/account-switch isolation, privileged-command parameter tampering/replay, LiveOps abuse and competitive-value isolation.
- Prove Game Master role authorization, privileged-operation validation and competitive isolation under adversarial conditions.

## Acceptance-only rule
T66 cannot patch production during the attack review. Every verified exploit reopens the owning production task, then T66 restarts against the repaired integrated candidate.
