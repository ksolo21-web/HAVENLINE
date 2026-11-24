# T20 — Road and vehicle customer service — Frozen Preparation Scope

**Preparation status:** PREPARED_GOVERNANCE_ONLY  
**Authoritative runtime status:** LOCKED  
**Prepared from:** `havenline/governance-t12-prep` @ `66efe083a57573b35fe4e6a3e8c9ab378d680796`

## Required outcome
- Add road arrival, vehicle queueing, service positioning, service completion/payment handoff and departure behavior.
- Preserve pedestrian routing and work lanes while proving vehicle/pedestrian collision separation.
- Keep camera composition readable at gameplay scale across queue growth and service peaks.
- Prove routing, queue recovery, clipping/turnaround, save/reload and representative-load performance.

## Explicit exclusions
No T53 inter-region transportation, no premium economy/store scope, and no customer-model replacement outside T15 interfaces without an accepted change request. Runtime activation waits for T15 and T17 approval/integration.

## Acceptance floor
Universal G1–G14 as applicable; mandatory dimensions strictly >9.0 unrounded, target 10/10; zero mandatory defects; exact-source evidence.
