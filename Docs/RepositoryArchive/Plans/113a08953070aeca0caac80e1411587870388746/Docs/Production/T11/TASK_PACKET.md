# T11 task packet — Camp construction and visual upgrade system

## Governance state

- **Parallel state now:** prepared for contract-bound isolated build/test while T09/T10 continue.
- **Highest legal pre-T10 state:** `BUILT_PENDING_DEPENDENCY`.
- **Final integration gate:** T05 + T10 must both be `APPROVED`; T10 must be integrated on `codex/havenline-sequential-task-01` before T11 can become `INTEGRATION_READY`.
- **Preparation branch:** `havenline/governance-t11-prep`.
- **Isolated builder branch:** `havenline/T11-camp-construction`.
- **Builder owner:** `camp-construction-builder`.
- **Prepared against T10 contract checkpoint:** `7e95338e339fb331a5d6b094874c15d5a7e96e16`.
- **Required critics after dependency reconciliation:** C2, C3, C4, C6.
- **Forward acceptance:** every mandatory dimension strictly `> 9.0` unrounded, target 10/10, applicable G1-G14 PASS, zero unresolved mandatory defects.

`FROZEN_SCOPE.md` T11-R15 and `BUILD_PENDING_POLICY.md` define the timing rule. Build-pending work is real candidate work, but it is not evidence of final T10 compatibility or task approval.

## Builder objective

Build Havenline's authored camp construction and visible upgrade content while treating T10 as the eventual authority for eligibility, exact-once transaction/debit/state transition and recovery. Until T10 is accepted, the T11 candidate uses a deterministic semantic mock/adapter matching the frozen T10 contract rather than editing or guessing T10 internals.

Reference B remains the visual anchor: winter field + in-world construction pad -> warm fenced work camp with a central heated vessel/fire, stock/counter space, readable routes and later visibly improved camp states. Existing T03 perimeter/gate authority is preserved; T11 does not duplicate or replace it.

## Approved content available now

Direct T11-approved T05 bindings:

- `hearth_vessel` — central heated station; approved `fx_heat`, `input`, `upgrade`, `worker` sockets.
- `pad_build` — yellow construction pad; approved `icon` and `interaction` sockets.
- `pad_upgrade` — orange upgrade pad; approved `icon` and `interaction` sockets.

Exact T05 paths, hashes, footprints and sockets are pinned in `T05_REUSE_BINDINGS.json`. Passive counter/stock assets may support composition only; their T16/T17 behavior stays excluded. T08 remains authoritative for real stock quantities.

The approved T03 gates/work lanes, T04 camera envelope and T07 contextual-control contract are hard constraints. `SPATIAL_BASELINE.json` and its automated tests enforce them.

## T11-owned candidate paths

- `HavenlineGodot/scripts/camp_construction.gd`
- `HavenlineGodot/scripts/camp_construction_view.gd`
- `HavenlineGodot/data/camp_upgrade_recipes.json`
- `HavenlineGodot/assets/camp_upgrades_v1/**`
- `HavenlineGodot/tests/test_task11_camp_construction.gd`
- `HavenlineGodot/tests/test_task11_integration.gd`
- `HavenlineGodot/tests/capture_task11_camp_upgrade.gd`
- `Docs/Production/T11/**`
- `tools/havenline/task11/**`
- `.github/workflows/havenline-task11-*.yml`

Protected from the T11 builder: T10 runtime/recipe files, T08/T09 runtime, T05 source assets, `main.gd`, `simulation.gd`, canonical integration registries, and later-task systems.

## Source contract

### `camp_construction.gd`

Content-domain adapter only:

1. load and validate T11 state/recipe bindings;
2. expose stable `camp_state_id`, presentation and asset-manifest identities;
3. call a dependency-injected T10-style preview port without mutation;
4. call the injected commit port with a stable transaction identity;
5. never debit resources or write transform/progression state directly;
6. map a completed transform state to exactly one authored camp stage;
7. reject malformed, duplicate, stale and incompatible bindings;
8. support deterministic tests/captures without extra gameplay controls;
9. separate test-only fixture prices from shipping provenance;
10. keep stable content identity for later persistence/recovery.

### `camp_construction_view.gd`

Presentation only:

- show blocked/ready/preview/committing/complete/error states truthfully;
- instantiate/switch the correct authored stage deterministically;
- preserve T03 routes/gates, T04 camera readability and T07 contextual action language;
- remove temporary transition effects/collision proxies;
- never debit resources, advance progression or own T10 state;
- do not rebuild unchanged completed states every frame.

### `camp_upgrade_recipes.json`

Every row includes:

- `camp_state_id`
- `t10_recipe_id`
- `source_camp_state`
- `target_camp_state`
- `presentation_key`
- `asset_manifest_key`
- `shipping`
- `route_clearance_profile`
- `camera_readability_profile`

Any shipping row additionally requires `price_source` or `tuning_record`. Until authoritative camp-price provenance exists, build-pending fixtures must be `shipping:false` + explicitly `test_only:true`. No reference-video number or unrelated historical furnace/barricade cost may be promoted silently.

## Build-pending tests to complete now

- deterministic recipe/state parsing and ordering;
- malformed/duplicate binding rejection;
- shipping recipe without price provenance fails closed;
- non-shipping test fixtures cannot masquerade as shipping;
- preview causes no geometry/resource/state mutation;
- one semantic mock commit maps to one target stage;
- duplicate/replay cannot duplicate camp geometry/effects;
- stale/out-of-order state rejects rather than guessing;
- reload/reconstruction maps deterministically to one stage;
- transition temporaries clean up;
- unchanged stage causes zero rebuild churn;
- player routes/gates/pads remain clear through each candidate stage;
- T04 camera target/readability envelope remains valid;
- T07 one-joystick/context behavior remains unchanged;
- no new required build button/menu/inventory grid/freeform placement mode;
- exact T05 bindings stay immutable;
- Godot import/build succeeds;
- bounded geometry/material/collision and transition cost.

## Build-pending evidence allowed now

- exact source/base and changed-file manifest;
- field/pad, candidate initial camp and visual-upgrade before/transition/after frames driven by the semantic mock;
- gameplay/overhead/three-quarter/detail route and pad readability frames;
- phone/tablet/foldable composition checks;
- geometry/material/collision/performance records;
- deterministic duplicate/replay/reconstruction evidence;
- clear disclosure that T10 reconciliation, shipping price provenance and final integration tests are pending.

This evidence may support internal build quality review, but final C2/C3/C4/C6 approval remains after T10 reconciliation.

## Promotion after T10 is accepted

1. Verify T10 is APPROVED/integrated and its completion record is authoritative.
2. Reconcile the T11 adapter and recipe IDs to the exact accepted T10 interface/source.
3. Supply authoritative price/tuning provenance for any recipe promoted to shipping.
4. Run `prepare_activation.py --activate --base <exact-post-T10-integration-head>`.
5. Apply/validate integration-owner reservation and rebase/reconcile the T11 candidate without losing approved work.
6. Rerun exact-once T10 integration, T08/T09-through-T10 conservation, affected evidence and impacted regression.
7. Pass G1 and candidate guards; only then mark `INTEGRATION_READY`.
8. Integrate through the integration owner, run G14 on the merged candidate, then independent C2/C3/C4/C6 and repair/retest until strict acceptance passes.

## Current blocker truth

T10 being unfinished **does not block T11 isolated build/test**. It blocks final promotion from `BUILT_PENDING_DEPENDENCY` to `INTEGRATION_READY`, final critics, canonical integration and approval.
