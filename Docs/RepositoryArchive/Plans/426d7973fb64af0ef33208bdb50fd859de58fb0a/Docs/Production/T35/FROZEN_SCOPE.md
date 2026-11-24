# T35 — Store, billing and entitlement system — Frozen Preparation Scope

**Preparation status:** PREPARED_GOVERNANCE_ONLY  
**Authoritative runtime status:** LOCKED

## Required outcome
- Build the future store/billing/entitlement boundary around verified platform purchase results, idempotent entitlement grants, restore/recovery, transparent prices, and failure-safe UX.
- Normal-player checkout and verification remain unchanged by Game Master privileges.
- Every approved SKU is zero-cost claimable by Game Master through a separate server grant path; GM claims must never invoke real-money checkout.

## Explicit exclusions
No VIP perk logic (T36), no LiveOps scheduling (T37), and no client-authoritative purchase success.

## Acceptance floor
G10 security/economy and G11 adaptive UI are mandatory; C11 included. Strict >9.0 unrounded.
