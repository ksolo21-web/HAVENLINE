# T10 dependency-independent prebuild

This branch is intentionally non-integratable while T09 is not APPROVED.

Allowed prebuild work is limited to T10-owned, T09-independent framework code, deterministic recipe/state contracts, exact-once/replay protection, preview purity, recovery semantics, fixture integration and evidence harnesses. No T09 runtime path may change and no T10 production approval/integration claim may be made.

## Latest verified checkpoint — 2026-09-16

- Prebuild branch: `prebuild/T10-world-transform`
- Exact verified runtime/test/capture source: `c38017f9c5545cb20e2795c7d6c4d1720980cb6f`
- CI run: `35080179136`
- CI result: **PASS**
- Formal T10 domain/adversarial checks: **104 / 104 PASS**, zero failures
- Fixture simulation integration/race checks: **30 / 30 PASS**, zero failures
- Stress load: **512 targets / 1,024 successful two-phase transactions**
- Stress elapsed time on CI: **53.71 ms** total for the 1,024-transaction fixture workload
- Stress static-memory growth on CI: **3,639,156 bytes**
- Full 512-target component-state export/import round-trip: PASS
- Full frozen T10 source-contract validator: PASS
- Rendered lifecycle evidence: **8 / 8 unique 1280x720 PNGs PASS**
- Lifecycle evidence states: `ready`, `preview`, `committing`, `complete`
- Lifecycle evidence views: `front`, `three-quarter`
- Governance/migration/production-tool regression: PASS
- Evidence artifact: `10439612457`
- Evidence ZIP SHA256: `21988cc3f10c06c1ca753528efb3d5cde79dc687e876a8371bc036c6c30ef257`
- Integration head observed by the exact run: `437f901b7478c0a20a90d9ed3627cbb5f76be4d9`
- T09 state observed by the exact run: `ASSIGNED`
- Active T10/T09 ownership collisions: `0`
- `integration_allowed`: false
- `task_approved`: false
- `real_t09_adapter_bound`: false

### What is implemented and proven before T09 closure

- Pure deterministic `preview_transform` with exact resource shortfalls and no caller/state mutation.
- Two-phase `commit_transform`: creates an idempotent debit intent but **does not** advance the world.
- World state advances only after `accept_authoritative_receipt` validates a simulation-confirmed debit.
- Exactly-once pending/completed transaction replay semantics.
- Transaction-ID collision rejection when an ID is reused for a different request.
- One in-flight transaction per target, preventing two transaction IDs from double-debiting the same target revision.
- An authoritative receipt must match an exact T10-prepared transaction; unsolicited well-formed simulation receipts fail closed.
- Altered-debit, malformed, forged-authority and stale/out-of-order invalid-state receipt rejection.
- Pending transaction persistence/recovery and idempotent resubmission after a crash/reload.
- Crash-window recovery for the case where simulation debited successfully but T10 crashed before accepting the receipt.
- Independent concurrent transactions for different targets, including out-of-order authoritative receipt arrival.
- Completed receipt replay protection after reload.
- Fail-closed component-state import with transactional rollback on malformed schema/revision/resource data.
- Component import rejects multiple pending transactions for the same target.
- Presentation lifecycle `locked -> ready -> preview -> committing -> complete`.
- Presentation cannot enter `complete` from a raw simulation-shaped receipt; it requires a receipt validated and stamped by T10.
- T11 final camp-content ownership and T14 global save/versioning ownership remain preserved.
- Deterministic identical-input/identical-receipt behavior is proven.

## Formal production-reservation alignment

The temporary `HavenlineGodot/tests/test_task10_prebuild.gd` path has been retired. All executable prebuild coverage now lives inside the frozen T10 production reservation:

- `HavenlineGodot/scripts/world_transform.gd`
- `HavenlineGodot/scripts/world_transform_view.gd`
- `HavenlineGodot/data/world_transform_recipes.json`
- `HavenlineGodot/tests/test_task10_world_transform.gd`
- `HavenlineGodot/tests/test_task10_integration.gd`
- `HavenlineGodot/tests/capture_task10_world_transform.gd`
- `Docs/Production/T10/**`
- `tools/havenline/task10/**`
- `.github/workflows/havenline-task10-*.yml`

The exact passing CI run confirmed no T09-owned path and no integration-only runtime path changed.

## Fixture integration seam

`test_task10_integration.gd` deliberately uses a `FakeSimulationAuthority`, not T09 production code. This lets T10 prove its side of the authority protocol while T09 is unfinished. It tests:

- same-target race blocking before any debit;
- exact authoritative resource debit and retry idempotency;
- rejection of unsolicited but well-formed receipts;
- stale preview/resource availability rejection by simulation without premature world advancement;
- eventual success of the same pending transaction when authoritative resources become available;
- crash after debit / before T10 receipt acceptance;
- multiple targets in flight together with out-of-order receipt arrival;
- persisted-state rejection of two pending transactions for one target.

This fixture does **not** certify the real T09 adapter. After T09 approval, the fake authority must be replaced/bound to the approved T09/T08 interfaces and the suite rerun.

## Lifecycle evidence review

The capture harness renders a deliberately simple framework fixture, not production camp art and not T11 content. It exists to prove lifecycle/readability/state transitions before T09 closure.

Exact verified evidence contains eight unique 1280x720 images: four lifecycle states from front and three-quarter views. Internal evidence-only visual review found:

- each lifecycle state is immediately distinguishable;
- state labels are legible;
- front and three-quarter views are unobstructed;
- fixture geometry remains readable against the background/floor;
- the evidence explicitly identifies itself as lifecycle evidence and **not T11 camp content**;
- no production-art quality claim is made from this fixture.

Internal lifecycle-evidence review score: **10.0 / 10 for evidence clarity and scope compliance only**. This is not C1/C2/C3/C4/C6/C7 production approval and is not a score for final game art.

## Internal review / repair history

The internal repair loop found and fixed five issues while T09 remained active:

1. **Atomicity defect:** the first executable version advanced T10 world state before the simulation debit was confirmed. Repaired to two-phase prepare -> simulation debit -> T10 validation -> world advance.
2. **Presentation trust defect:** a merely simulation-shaped receipt could have visually completed the transformation. Repaired so completion requires `accepted_by_world_transform`.
3. **Same-target concurrency defect:** two transaction IDs could be prepared against one target revision before either receipt returned. Repaired with one in-flight transaction per target.
4. **Unsolicited-receipt defect:** a valid-looking simulation receipt not prepared by T10 could advance state. Repaired by requiring exact prepared-transaction matching.
5. **Capture tooling defect:** three dynamically inferred locals caused the first Xvfb/Vulkan capture script to fail parsing. Repaired with explicit `Dictionary` typing; the subsequent exact-source run produced all eight images and passed governance.

The exact repaired dependency-independent source passed all listed gates. Internal dependency-independent prebuild review score: **10.0 / 10 for this isolated scope only**.

## Required after T09 becomes APPROVED

1. Reconcile this prebuild onto the **exact post-T09 integration head**.
2. Run T10 activation preflight and register the production T10 builder/base/reservation.
3. Replace/bind `FakeSimulationAuthority` assumptions to the real approved T09/T08 simulation adapter and authoritative debit/harvest interfaces.
4. Rerun the formal T10 domain + real integration suites and all impacted T01-T09 regression.
5. Add final transformation presentation/evidence/assets without stealing T11 camp-building content.
6. Run save/recovery/device/performance evidence on the integrated candidate and exact production capture.
7. Run required independent C1/C2/C3/C4/C6/C7 critics; every mandatory dimension must be strictly >9.0 unrounded with zero unresolved mandatory defects.
8. Only the reconciled, integrated, post-T09 candidate may become T10 APPROVED.
