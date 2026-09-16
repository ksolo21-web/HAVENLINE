# T10 dependency-independent prebuild

This branch is intentionally non-integratable while T09 is not APPROVED.

Allowed prebuild work is limited to T10-owned, T09-independent framework code, deterministic recipe/state contracts, exact-once/replay protection, preview purity, recovery semantics, and isolated tests using fixtures. No T09 runtime path may change and no T10 approval/integration claim may be made.

## Verified checkpoint — 2026-09-16

- Prebuild branch: `prebuild/T10-world-transform`
- Exact verified runtime/test source: `fbb3c656f5b62040addcc8efca7e082cdd72d03c`
- CI run: `35078425757`
- CI result: PASS
- Isolated Godot checks: **82 / 82 PASS**, zero failures
- Governance/migration/production-tool regression: PASS
- Evidence artifact: `10439316240`
- Evidence ZIP SHA256: `a09c668008056b784bf4acca08f303858306369938ba6b27702378a77bf13532`
- T09 state observed by the exact run: `ASSIGNED`
- `integration_allowed`: false
- `task_approved`: false
- `t09_adapter_bound`: false

### Implemented and proven before T09 closure

- Pure deterministic `preview_transform` with exact resource shortfalls and no caller/state mutation.
- Two-phase `commit_transform`: creates an idempotent debit intent but **does not** advance the world.
- World state advances only after `accept_authoritative_receipt` validates a simulation-confirmed debit.
- Exact-once transaction replay protection for pending and completed transactions.
- Transaction-ID collision rejection when an ID is reused for a different request.
- Altered-debit and untrusted-receipt rejection without consuming prepared state.
- Pending transaction persistence/recovery and idempotent resubmission after a crash/reload.
- Completed receipt replay protection after reload.
- Fail-closed component-state import with transactional rollback on malformed schema/revision data.
- Presentation lifecycle `locked -> ready -> preview -> committing -> complete`.
- Presentation cannot enter `complete` from a raw simulation-shaped receipt; it requires a receipt validated and stamped by T10.
- T11 final camp-content ownership and T14 global save/versioning ownership remain preserved.
- Deterministic identical-input/identical-receipt behavior is proven.

### Internal review / repair loop

The first executable prebuild passed 54/54 checks, but internal review found a mandatory atomicity defect: the first implementation advanced T10 world state during `commit_transform` before simulation had confirmed the resource debit. That could leave world state and inventory inconsistent after a debit failure or crash.

The implementation was repaired to a two-phase transaction: prepare idempotent debit intent -> authoritative simulation debit receipt -> T10 validates receipt -> world state advances -> presentation may complete. A second review also hardened presentation so a merely simulation-shaped/forged receipt cannot visually complete a transformation before T10 accepts it.

The repaired exact source then passed 82/82 checks and all prebuild governance gates. Internal prebuild-core review score: **10.0/10 for this dependency-independent scope only**. This is not an independent C1/C2/C3/C4/C6/C7 production approval and does not approve T10.

## Required after T09 becomes APPROVED

1. Reconcile this prebuild onto the **exact post-T09 integration head**.
2. Run T10 activation preflight and register the production T10 builder/base/reservation.
3. Replace fixture assumptions with the real approved T09/T08 simulation adapter and authoritative debit/harvest interfaces.
4. Convert/extend the prebuild test into the formal T10 world-transform + integration suites.
5. Add final transformation presentation/evidence without stealing T11 camp-building content.
6. Run full impacted T01-T09 regression, save/recovery/device/performance evidence, and exact-source capture.
7. Run required C1/C2/C3/C4/C6/C7 critics; every mandatory dimension must be strictly >9.0 unrounded with zero unresolved mandatory defects.
8. Only the integrated post-T09 candidate may become T10 APPROVED.
