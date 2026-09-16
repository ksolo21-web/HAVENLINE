# T10 isolated build status — BUILT_PENDING_DEPENDENCY

T10 is fully buildable/testable in isolation under the controlled parallel-production model while T09 remains active. The dependency blocks `INTEGRATION_READY`, real T09/T08 binding, production critic execution, integration and approval — not isolated construction or hardening.

## Current exact hardened checkpoint — 2026-09-16

- Builder branch: `havenline/T10-world-transformation`
- Exact verified candidate: `f5283f56d96af3ddad9c3adb87db286bbadb73ec`
- Isolated CI run: `35104414502`
- Isolated CI result: **PASS**
- Declared isolated state: **`BUILT_PENDING_DEPENDENCY`**
- T09 state observed by the exact run: `ASSIGNED`
- `integration_allowed`: `false`
- `real_t09_adapter_bound`: `false`
- `task_approved`: `false`
- `isolated_critic_input_ready`: `true`
- Production critic execution allowed before dependency handoff: `false`
- Active T10/T09 ownership collisions: `0`
- Evidence artifact: `10449387994`
- Evidence artifact size: `9,648,859` bytes
- Evidence ZIP SHA256: `61acbbe1c29a65873d8bcaa22c07228256bf6785966cf6465f50660f27d34665`
- Integration head observed by the exact run: `5f45c8429312ae8469be185321bf1b5d9b98a915`

## Exact executable evidence

- Formal T10 domain/adversarial checks: **154 / 154 PASS**, zero failures.
- Fixture-authority integration + R11 presentation checks: **60 / 60 PASS**, zero failures.
- 5,000 repeated previews: PASS, zero component-history growth; exact run elapsed **48.285 ms**.
- 5,000 rejected commits: PASS, zero prepared/receipt-history growth; exact run elapsed **66.807 ms**.
- Neutral large-catalog stress: **258 recipes**, deterministic branching; exact run elapsed **6.837 ms**.
- Transformation stress: **512 targets / 1,024 successful two-phase transformations**; exact run elapsed **168.374 ms**.
- Completed-history bound after stress: **512 latest receipts** for 512 targets.
- Static-memory delta during stress: **2,341,652 bytes**.
- Full 512-target component snapshot/import round-trip: PASS.
- Same-target race protection, unsolicited receipt rejection, stale-authority rejection, crash-after-debit recovery, out-of-order multi-target receipts: PASS.
- Frozen T10 source-contract validator: PASS.
- Baseline lifecycle evidence: **10 / 10 unique 1280x720 renders** PASS.
- Havenline device matrix: **6 / 6 configurations, 12 / 12 exact-size renders** PASS.
- Native scale-1 critic evidence: **30 / 30 unique 3840x2160 renders** PASS.
- Native evidence states: `ready`, `blocked`, `preview`, `committing`, `complete`.
- Native evidence cameras: `front`, `side`, `three-quarter`, `overhead`, `gameplay`, `detail`.
- Critic-input readiness validator for C1/C2/C3/C4/C6/C7: PASS with zero missing evidence markers.
- Production registry/migration/tool regression: PASS.

## R01/R07 recipe-graph hardening

The isolated candidate now enforces progression integrity at catalog load instead of trusting future content authors to avoid invalid graphs.

- Duplicate recipe IDs fail closed.
- Missing source/target fields fail closed.
- Zero/negative costs fail closed.
- Duplicate resource-cost rows and duplicate prerequisites fail closed.
- Implicit self-transitions fail closed; explicitly declared self-transitions may be modeled.
- Inverse metadata without `reversible:true` fails closed.
- A reversible recipe must name an existing reciprocal inverse.
- Reciprocal inverse endpoints must exactly reverse source/target states.
- Undeclared two-state and multi-state progression cycles fail closed.
- Explicit inverse-pair states are collapsed as one reversible progression group; all ordinary edges between groups must remain acyclic.
- A valid reciprocal reversible pair was executed forward and backward with its declared costs and monotonically increasing target revisions.
- Failed cyclic reconfiguration is transactional and leaves the previously valid catalog unchanged.

These rules close the mandatory R07 gap that previously allowed an undeclared cycle/downgrade catalog to configure successfully.

## Reusable R11 world-response layer

`HavenlineGodot/scripts/world_transform_view.gd` remains presentation-only and T11-safe. It owns a neutral ring, preview volume and status beacon with shape+color redundancy, bounded committing pulse, exact blocked reasons/shortfalls and readability scale `0.85–1.35`.

The exact candidate still proves a strict **4 visual nodes / 1 visual build** through repeated lifecycle updates. It never owns shared resource counts or progression and cannot enter `complete` from a raw simulation-shaped receipt; completion requires T10 acceptance of the authoritative receipt.

## Native 4K evidence review

The critic-ready fixture renders five lifecycle states across six meaningful camera classes at exact **3840x2160 scale-1**. The target itself remains neutral gray; lifecycle response comes from the T10 view.

An internal pixel review found the first detail-camera evidence too tight because it clipped the state title. That evidence defect was repaired by widening/repositioning the detail camera and the complete 30-frame set was regenerated. The repaired set was visually rechecked: the detail title/disclaimer remain fully inside frame in all five states and the full front/side/three-quarter/overhead/gameplay/detail matrix remains readable. This is evidence-quality review only, not a C1/C2/C3/C4/C6/C7 production score.

## Critic-input readiness

`tools/havenline/task10/validate_critic_readiness.py` validates the source-bound isolated evidence needed by required critics C1/C2/C3/C4/C6/C7. It intentionally assigns **no critic score** and cannot approve T10.

The exact candidate reports `isolated_critic_input_ready:true`. Remaining production-review dependencies are limited to the real post-T09 integrated candidate/provenance, real T09/T08 authority binding, impacted gameplay regression, affected recapture if integration changes visuals, post-integration performance regression, and the actual independent production critic execution.

## Correct dependency boundary

T10 may continue receiving isolated fixes, tests, performance work, capture improvements, neutral assets and internal evidence review while T09 is unfinished, provided work stays inside the frozen T10 reservation and fixture contracts do not pretend to certify the real T09 adapter.

The following remain blocked until T09 and required earlier dependencies are approved/integrated:

1. reconcile T10 onto the **exact post-T09 integration head**;
2. formally register/confirm production T10 ownership against that exact base;
3. replace fixture authority assumptions with the real approved T09/T08 authority interfaces;
4. rerun full real integration and impacted T01–T09 regression;
5. recapture any evidence affected by reconciliation/binding;
6. execute required C1/C2/C3/C4/C6/C7 production reviews at strict `>9.0` unrounded with zero mandatory defects;
7. promote from `BUILT_PENDING_DEPENDENCY` to `INTEGRATION_READY`;
8. integrate through the integration owner and pass merged-candidate regression before `APPROVED`.

The global candidate guard and the integration-candidate workflow are expected to remain red before that dependency handoff because they enforce the post-T09 registration/base requirement. They are integration-boundary guards and must not be weakened merely to make the isolated branch green.
