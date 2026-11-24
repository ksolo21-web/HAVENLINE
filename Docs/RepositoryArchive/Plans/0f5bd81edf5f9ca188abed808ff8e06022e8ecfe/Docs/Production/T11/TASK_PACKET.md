# T11 task packet — Camp construction and visual upgrade system

## Governance state

- **Preparation mode:** dependency-safe parallel prep while T09/T10 remain unfinished.
- **Production status target now:** governance prepared only; T11 remains `LOCKED` in authoritative production state until T10 is approved/integrated.
- **Production implementation gate:** T05 + T10 must both be `APPROVED` on the authoritative integration branch.
- **Prepared branch:** `havenline/governance-t11-prep`.
- **Prepared on top of:** reviewed T10 prep checkpoint `7e95338e339fb331a5d6b094874c15d5a7e96e16`, so T11 is bound to the prepared T10 public contract without claiming T10 runtime completion.
- **Future isolated builder branch:** `havenline/T11-camp-construction`.
- **Future owner:** `camp-construction-builder`.
- **Activation base:** the exact integration commit that records T10 approval/integration.
- **Planned reservation:** `@reservation:T11` from `FROZEN_SCOPE.md` / `ACTIVATION_CHECKLIST.json`.
- **Evidence path after activation:** `Docs/Production/Evidence/T11/`.
- **Required critics:** C2, C3, C4, C6.
- **Forward gate:** every mandatory dimension strictly `> 9.0` unrounded, target `10.0`, all applicable G1-G14 and impacted regression PASS, zero unresolved mandatory defects.
- **Machine-readable preparation:** `PREBUILD_CONTRACT.json` locks reference moments, capture groups, route checks, critic coverage and shipping-price provenance.
- **Exact T05 reuse:** `T05_REUSE_BINDINGS.json` pins approved T05 asset IDs, source paths, SHA-256 values, footprints, sockets and later-task behavior boundaries.
- **Preparation QA:** `tools/havenline/task11/tests/` proves fail-closed activation, exact T05 binding integrity and zero `HavenlineGodot/` runtime changes during preparation.

## Builder objective after activation

Use the approved T10 World Transformation Framework to implement Havenline's authored camp construction and visible upgrade content without duplicating transaction logic. T11 must create readable in-world construction pads, the actual first camp state and later camp visual upgrades while preserving navigation, automatic contextual controls, resource truth and reference-grounded presentation.

The authoritative visual anchor is Reference B: winter field + construction pad -> fenced warm work area with a central heated vessel/fire zone, stock/counter area, readable gates/lanes and visible subsequent camp improvement. T11 must not absorb customer, combat, defense, progression or persistence ownership from later tasks.

## Approved T05 content available to T11

Direct T11 bindings already authored and approved by T05 are:

- `hearth_vessel` — central heated-vessel/fire visual anchor, with `fx_heat`, `input`, `upgrade`, and `worker` sockets;
- `pad_build` — yellow diamond construction pad with `icon` and `interaction` sockets;
- `pad_upgrade` — orange triangular upgrade pad with `icon` and `interaction` sockets.

Their exact approved paths, hashes, footprints, triangle counts, sockets and visual variants are pinned in `T05_REUSE_BINDINGS.json`. T11 may reference/place them but may not modify the approved `stations_v2` source assets.

T05 also contains counters/stock-pad assets that can be used only as passive composition/readability fixtures where appropriate. T11 does **not** receive their later T16/T17 behavior. T08 remains authoritative for real resource-stack quantities; T11 may not create fake duplicate stockpiles merely for visuals.

## Required source contract

### `camp_construction.gd`

Content-domain adapter only:

1. load/validate T11 camp-state and T10 recipe bindings;
2. expose stable camp state IDs and presentation keys;
3. request pure eligibility/preview from T10;
4. request commit through T10 with stable transaction identity supplied by the integration layer;
5. never debit resources or write T10 authoritative state directly;
6. map a completed T10 state to exactly one authored camp-state identity;
7. reject missing, duplicate or incompatible state/recipe bindings;
8. expose deterministic capture/test hooks without adding gameplay controls;
9. keep shipping pricing provenance separate from test-only fixture values;
10. expose stable content identity for later T14 persistence without defining the global save schema.

### `camp_construction_view.gd`

Presentation only:

- show blocked/ready/preview/committing/complete states using in-world pads and authored camp visuals;
- instantiate/switch the correct authored camp stage deterministically;
- preserve T03 routes/gates, T04 camera readability and T07 contextual action language;
- clean up temporary transition effects/collision proxies after completion;
- never debit resources, advance progression or mutate T10 transform state;
- avoid rebuilding unchanged completed states every frame.

### `camp_upgrade_recipes.json`

Each registered camp stage must include fields equivalent to:

- `camp_state_id`
- `t10_recipe_id`
- `source_camp_state`
- `target_camp_state`
- `presentation_key`
- `asset_manifest_key`
- `shipping` boolean
- `price_source` / `tuning_record` for shipping content
- `route_clearance_profile`
- `camera_readability_profile`

Validation rejects duplicate state IDs, duplicate recipe binding, missing source/target stage assets, shipping prices without provenance, impossible/self transitions not explicitly modeled, missing route profiles and bindings to unknown T10 recipes.

## Mandatory implementation matrix

### Content/state tests

- deterministic camp-state parsing and ordering;
- duplicate/malformed state/recipe binding rejection;
- shipping recipe missing price provenance fails closed;
- test-only fixture may use explicit non-shipping values and can never be promoted silently;
- blocked/ready preview produces no geometry/state/resource mutation;
- one valid T10 commit switches to exactly one target camp stage;
- duplicate/replayed T10 commit cannot spawn duplicate camp structures/effects;
- stale/out-of-order state is rejected rather than guessing the next camp stage;
- completed state reload/reconstruction produces the same authored camp stage once;
- all temporary transition objects are released after completion;
- unchanged state causes zero repeated rebuild churn.

### Route/camera/control tests

- player route through gate remains traversable before and after construction;
- required pads remain reachable/readable at gameplay scale;
- no stage traps the player or blocks mandatory work lanes;
- T04 camera remains within accepted composition/readability behavior;
- T07 single-joystick/context action behavior remains unchanged;
- no new required action button, inventory grid, build menu or freeform placement mode appears;
- adaptive layouts keep pad costs/status and active world state readable.

### Integration tests after T10 approval

- T11 only calls the published T10 preview/commit/state contract;
- T11 does not edit/debit T08 or T09 resource state directly;
- exact-once charge/state behavior remains owned and verified by T10;
- exact T11-direct T05 bindings are verified against the approved catalog before use;
- passive counter/stock-pad composition never activates T16/T17 behavior;
- approved T01-T10 regression remains clean;
- later T12/T13/T15/T21/T22 can consume T11 state without T11 pre-implementing their systems.

### Visual/capture evidence

- winter-field construction pad / blocked state;
- ready/preview state with readable in-world cost/status;
- active construction transition;
- completed initial camp from gameplay camera;
- overhead, side/three-quarter and detail views of completed camp;
- every registered shipping camp upgrade before/transition/after;
- gate/lane/pad reachability views;
- replay/duplicate attempt leaves completed state unchanged with no duplicate geometry;
- adaptive phone/tablet/foldable layouts;
- native 3840x2160 scale-1 evidence where applicable;
- exact-source geometry/material/performance records.

## Acceptance dimensions by critic

- **C2 Technical / Visual Integrity:** authored structures/materials/collision/ground contact are finished and consistent across views/states; no duplicate, seam, clipping or transition-cleanup defects.
- **C3 Havenline Gameplay Identity:** camp construction remains movement/proximity/context driven, physical and visually integrated; no control-heavy building game or hidden-menu substitute.
- **C4 Gameplay UX / Readability:** cost/readiness, actionable pad, transition result, routes and next interaction remain obvious at gameplay scale across adaptive layouts.
- **C6 Performance:** completed camp stages are stable/mostly static, transition effects clean up, geometry/material/collision budgets preserve headroom and no unchanged-state rebuild loop exists.

## Protected boundaries

Do not edit from the T11 builder branch unless an approved structured ChangeRequest authorizes it:

- T10 runtime transaction/state files and `world_transform_recipes.json`;
- T08 inventory/carrying runtime;
- T09 harvesting runtime;
- T05 approved source assets (reference/reuse only);
- `HavenlineGodot/scripts/main.gd`;
- `HavenlineGodot/scripts/simulation.gd`;
- canonical shared registries owned by integration;
- T12/T13 progression/difficulty systems;
- T14 global persistence/versioning;
- T15 customer population/routing;
- T21 weapon/combat progression;
- T22 functional defensive structures.

## Parallel-prep work allowed before T10 approval

Allowed now:

- freeze T11 scope and task packet;
- define future disjoint ownership paths;
- define camp-state/recipe/presentation contracts;
- bind exact approved T05 reusable asset IDs/hashes/footprints/sockets and behavior-owner boundaries;
- map authoritative reference moments and future capture groups;
- prepare validation and candidate CI scaffolding;
- test that activation fails closed while T10 is unfinished;
- prepare an activation tool that refuses activation until T05/T10 are APPROVED and T10 is integrated;
- static collision/review against T05/T08/T09/T10 and integration-only paths.

Not allowed now:

- claim T11 runtime implementation as `ASSIGNED` or `BUILDING_ISOLATED`;
- create/modify shipping camp runtime/assets and present them as a candidate;
- edit T10 runtime semantics;
- invent shipping prices merely to unblock construction.

## Activation handoff

When T10 is integrated and marked APPROVED, run the T11 activation preflight against the exact new integration head. It must fail on stale base, unapproved dependency, stale T10 owner, conflicting reservation or missing T10 completion record. Reconcile the prepared T11 interface assumptions against T10's exact accepted public contract. After a clean preflight, apply `@reservation:T11`, claim T11 as `ASSIGNED`, cut `havenline/T11-camp-construction` from the exact post-T10 governance checkpoint, run registry/candidate guards, then begin the builder/critic loop.

See `ACTIVATION_CHECKLIST.json`, `PREBUILD_CONTRACT.json`, `T05_REUSE_BINDINGS.json`, `defect-ledger.json`, and `tools/havenline/task11/prepare_activation.py`.
