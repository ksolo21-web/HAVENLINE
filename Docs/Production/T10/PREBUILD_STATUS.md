# T10 dependency-independent prebuild

This branch is intentionally non-integratable while T09 is not APPROVED.

Allowed prebuild work is limited to T10-owned, T09-independent framework code, deterministic recipe/state contracts, exact-once/replay protection, preview purity, bounded recovery/history semantics, fixture integration, reusable neutral world-response presentation, device-layout validation and evidence harnesses. No T09 runtime path may change and no T10 production approval/integration claim may be made.

## Latest verified checkpoint — 2026-09-16

- Prebuild branch: `prebuild/T10-world-transform`
- Exact verified runtime/test/capture/workflow source: `2c8987d0351536cd00c6031d4eada4a8c12bae00`
- CI run: `35082800871`
- CI result: **PASS**
- Formal T10 domain/adversarial checks: **130 / 130 PASS**, zero failures
- Fixture simulation integration + R11 world-response checks: **60 / 60 PASS**, zero failures
- Repeated-preview stress: **5,000 previews**, zero component-history growth
- Rejected-commit stress: **5,000 rejected commits**, zero prepared/receipt history growth
- Neutral catalog stress: **258 recipes** including explicit branching fixtures
- Transformation stress: **512 targets / 1,024 successful two-phase transactions**
- Retained completed history after 1,024 transactions: **512 latest receipts** — one per target
- Stress elapsed time on CI: **131.676 ms** total for the 1,024-transaction fixture workload
- Stress static-memory growth on CI: **2,341,652 bytes**
- 5,000-preview elapsed time: **35.775 ms**
- 5,000-rejected-commit elapsed time: **50.307 ms**
- 258-recipe configure/preview elapsed time: **3.879 ms**
- Full 512-target component-state export/import round-trip: PASS
- Full frozen T10 source-contract validator: PASS
- Baseline rendered lifecycle evidence: **10 / 10 unique 1280x720 PNGs PASS**
- Baseline lifecycle states: `ready`, `blocked`, `preview`, `committing`, `complete`
- Baseline evidence views: `front`, `three-quarter`
- Havenline device-layout matrix: **6 / 6 device configurations PASS**
- Device-layout evidence: **12 / 12 exact-size renders PASS** (`preview` + `committing` per device)
- Device classes covered: `phone`, `tablet`, `foldable`
- Matrix safe-area-flagged entry carried through evidence: `phone_20_9`
- Governance/migration/production-tool regression: PASS
- Evidence artifact: `10441032206`
- Evidence artifact bytes: `2,114,271`
- Evidence ZIP SHA256: `8532c23a88df4b4a4dc11da6722d7a9233f4d3511a5684a5f0b5fe4575c91a91`
- Integration head observed by the exact run: `5f45c8429312ae8469be185321bf1b5d9b98a915`
- T09 state observed by the exact run: `ASSIGNED`
- Active T10/T09 ownership collisions: `0`
- `integration_allowed`: false
- `task_approved`: false
- `real_t09_adapter_bound`: false

### What is implemented and proven before T09 closure

- Pure deterministic `preview_transform` with exact resource shortfalls and no caller/state mutation.
- Two-phase `commit_transform`: creates an idempotent debit intent but **does not** advance the world.
- World state advances only after `accept_authoritative_receipt` validates a simulation-confirmed debit.
- A request-scoped `authority_transaction_key` is derived from the transformation request plus target revision, so authoritative debit idempotency does not depend on a caller-chosen label.
- Exactly-once pending/completed transaction replay semantics.
- Transaction-ID collision rejection when an ID is reused for a different request.
- One in-flight transaction per target, preventing two transaction IDs from double-debiting the same target revision.
- An authoritative receipt must match an exact T10-prepared transaction; unsolicited well-formed simulation receipts fail closed.
- Altered-debit, malformed, forged-authority and stale/out-of-order invalid-state receipt rejection.
- Pending transaction persistence/recovery and idempotent resubmission after a crash/reload.
- Crash-window recovery for the case where simulation debited successfully but T10 crashed before accepting the receipt.
- Independent concurrent transactions for different targets, including out-of-order authoritative receipt arrival.
- Bounded completed history: only the latest completed receipt per target is retained; older transaction retries fail closed after the target advances.
- Fail-closed component-state import with transactional rollback on malformed schema/revision/resource/idempotency data.
- Component import rejects multiple pending transactions or multiple retained completed receipts for the same target.
- Neutral branching semantics and large-catalog behavior are proven without shipping T11 content.
- T11 final camp-content ownership and T14 global save/versioning ownership remain preserved.
- Deterministic identical-input/identical-receipt behavior is proven.

## Reusable R11 world-response layer

`HavenlineGodot/scripts/world_transform_view.gd` now owns a reusable presentation-only response layer instead of leaving lifecycle visualization to the capture harness.

The frozen five-state core remains `locked -> ready -> preview -> committing -> complete`, with `blocked` as an auxiliary failure/readiness state. The reusable neutral response is deliberately not camp/build content and consists of:

- a perimeter state ring;
- a translucent preview volume;
- a status beacon;
- state-specific shape + color redundancy;
- a bounded committing pulse;
- exact blocked reasons and resource shortfalls;
- a configurable world-space readability scale limited to `0.85–1.35`;
- a strict **4-node visual budget** including the response root;
- exactly **1 visual build** across repeated lifecycle transitions.

Direct executable checks prove locked/ready/blocked/preview/committing/complete visibility rules, readability bounds, pulse behavior, blocked-state payload preservation/clearance, presentation-only authority, and zero visual-node growth across repeated updates.

## Rendered lifecycle evidence

The target fixture remains static neutral gray. Lifecycle feedback comes from `world_transform_view.gd` itself; the capture harness does not recolor the target.

The exact verified baseline evidence contains 10 unique 1280x720 frames: five states from front and three-quarter views. Internal evidence-only review found:

- `ready`: blue-gray ring/beacon response;
- `blocked`: red response with a flattened beacon and no preview ghost;
- `preview`: amber ring/ghost volume;
- `committing`: blue response with active beacon/preview volume;
- `complete`: green response with emphasized beacon and no preview ghost;
- the neutral target remains unchanged across states;
- labels and response geometry remain readable from both review angles;
- evidence explicitly identifies itself as view-owned lifecycle evidence and **not T11 camp content**.

Internal lifecycle-evidence review score: **10.0 / 10 for evidence clarity and scope compliance only**. This is not C1/C2/C3/C4/C6/C7 production approval and is not a final-art score.

## Havenline device-layout matrix evidence

The CI gate reads `Docs/Production/DEVICE_LAYOUT_MATRIX.json` directly instead of inventing resolutions. It rendered T10 `preview` and `committing` at every required landscape logical viewport:

- `phone_16_9` — `2400x1080`
- `phone_20_9` — `2400x1080` and flagged by the matrix for safe-area testing
- `tablet_16_10` — `2560x1600`
- `tablet_4_3` — `2732x2048`
- `foldable_outer` — `2520x1080`
- `foldable_inner` — `2208x1768`

All 12 captures matched the exact matrix size and every device visibly distinguished `preview` from `committing`. The matrix currently gives `phone_16_9` and `phone_20_9` the same `2400x1080` logical viewport, so identical pixels are allowed only when both logical size **and lifecycle state** are identical. Duplicates across different sizes or different lifecycle states remain a hard failure. The exact verified run observed one permitted duplicate group: the two phone `preview` frames at `2400x1080`.

This verifies T10 world-space framing/readability across the project matrix. It does **not** invent an OS safe-area inset that the matrix does not specify, so it is not a claim that platform-specific inset handling has been simulated.

## Formal production-reservation alignment

The temporary `HavenlineGodot/tests/test_task10_prebuild.gd` path was retired. All executable prebuild coverage lives inside the frozen T10 production reservation:

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

`test_task10_integration.gd` deliberately uses a `FakeSimulationAuthority`, not T09 production code. The fixture simulation deduplicates by T10's request-scoped `authority_transaction_key` and proves T10's side of the contract while T09 is unfinished.

It covers same-target race blocking before debit, exact authoritative debit, retry idempotency, unsolicited receipt rejection, stale resource availability, eventual pending-transaction success, crash-after-debit recovery, different targets in flight simultaneously, out-of-order receipt delivery, bounded receipt history, and the reusable R11 presentation layer.

This fixture does **not** certify the real T09 adapter. After T09 approval, the fake authority must be replaced/bound to the approved T09/T08 interfaces and the same suite rerun.

## Internal review / repair history

The internal repair loop found and fixed these issues while T09 remained active:

1. **Atomicity defect:** initial world state advanced before the simulation debit was confirmed. Repaired to two-phase prepare -> simulation debit -> T10 validation -> world advance.
2. **Presentation trust defect:** a merely simulation-shaped receipt could visually complete. Repaired so completion requires `accepted_by_world_transform`.
3. **Same-target concurrency defect:** two transaction IDs could be prepared against one target revision. Repaired with one in-flight transaction per target.
4. **Unsolicited-receipt defect:** a valid-looking simulation receipt not prepared by T10 could advance state. Repaired by requiring exact prepared-transaction matching.
5. **Capture tooling defect:** dynamically inferred locals caused the first Xvfb/Vulkan capture script to fail parsing. Repaired with explicit `Dictionary` typing.
6. **R12 history-growth defect:** retaining every completed receipt caused event/history growth proportional to transaction count. Repaired with request-scoped authority idempotency keys plus latest-completed-receipt-per-target retention. The 1,024-transaction stress now retains 512 receipts for 512 targets, while 10,000 preview/rejection attempts create zero history.
7. **Device-matrix gate defect:** the first matrix gate incorrectly required all 12 PNG hashes to be unique even though two matrix rows intentionally share the same `2400x1080` logical viewport. Repaired so duplicates are allowed only for the same logical size + same lifecycle state, while each device must still distinguish `preview` from `committing`.

The exact repaired dependency-independent source passed every listed gate. Internal dependency-independent prebuild review score: **10.0 / 10 for this isolated pre-T09 scope only**.

## Required after T09 becomes APPROVED

1. Reconcile this prebuild onto the **exact post-T09 integration head**.
2. Run T10 activation preflight and register the production T10 builder/base/reservation.
3. Replace/bind `FakeSimulationAuthority` assumptions to the real approved T09/T08 simulation adapter and authoritative debit/harvest interfaces.
4. Rerun the formal T10 domain + real integration suites and all impacted T01-T09 regressions.
5. Bind final transformation content/assets/evidence to the integrated gameplay without stealing T11 camp-building content.
6. Rerun save/recovery/device/performance evidence on the integrated candidate and exact production capture.
7. Run required independent C1/C2/C3/C4/C6/C7 critics; every mandatory dimension must be strictly >9.0 unrounded with zero unresolved mandatory defects.
8. Only the reconciled, integrated, post-T09 candidate may become T10 APPROVED.
