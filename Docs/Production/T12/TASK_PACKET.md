# T12 task packet — Level 1–100 progression architecture

## Governance state

- **Preparation mode:** dependency-safe parallel prep while T11 remains unfinished.
- **Production status target now:** governance prepared only; T12 remains `LOCKED` until T07, T08, T10 and T11 are all approved and T10/T11 are integrated.
- **Current dependency checkpoint (2026-09-21):** T07 APPROVED, T08 APPROVED, T10 APPROVED/integrated at `eba0107def258824549fb10d81785290d0c81d97`; T11 is `ASSIGNED` on `havenline/T11-camp-construction` from base `f558b9b162b349d1ee127e65edf967f6d28dfed0` and is not integrated.
- **Prepared branch:** `havenline/governance-t12-prep`.
- **Preparation provenance:** originally prepared against `havenline/governance-t11-prep` checkpoint `b383e450594d60b172d43ed2d60bda535ca9f225`; T10 binding is now reconciled to its accepted integrated source while T11 remains provisional.
- **Future isolated builder branch:** `havenline/T12-progression-architecture`.
- **Future owner:** `progression-architecture-builder`.
- **Activation base:** exact integration commit that records T11 approval/integration and all dependencies approved.
- **Planned reservation:** `@reservation:T12` from `FROZEN_SCOPE.md` / `ACTIVATION_CHECKLIST.json`.
- **Evidence path after activation:** `Docs/Production/Evidence/T12/`.
- **Required critics:** C2, C3, C4, C6, C7.
- **Forward gate:** every mandatory dimension strictly `> 9.0` unrounded, target `10.0`, all applicable G1–G14 and impacted regression PASS, zero unresolved mandatory defects.
- **Parallel rule:** T11 runtime work and T12 governance preparation may proceed concurrently only with disjoint path ownership; production integration remains serial and integration-owner controlled.

## Builder objective after activation

Implement a deterministic Level 1–100 progression architecture that gives every level a meaningful progression role and supplies stable contracts for visible improvement, approximately ten-level milestones, connected-region progression and later difficulty/economy/save/content systems. The architecture must remain simple to the player, spend-blind, data-driven and compatible with Havenline's physical MOVE → AUTO-INTERACT → GATHER → CARRY → DELIVER → TRANSFORM → RESCUE → BUILD/UPGRADE → EXPLORE → DEFEND language.

T12 is architecture, not the later content itself. It must expose stable level/milestone/event/region-band identities and eligibility results without implementing T13 adaptive difficulty, T14 persistence, T33+ economy/monetization or T44–T52 region content.

### Preactivation buildout now frozen

The preparation package goes beyond a structural matrix without creating shipping runtime:

- `AUTHORING_BLUEPRINT.json` deterministically expands all 100 levels into stable level/slot/fact-slot/effect/hook/milestone/event identities.
- `BINDING_SLOT_CATALOG.json` freezes the allowed authoritative fact kinds for every fact slot and records approved T07/T08/T10 contract hints while keeping T11 IDs empty.
- `FACT_SLOT_BINDING_INDEX_TEMPLATE.json` predeclares all 99 Level 2–100 binding rows; exact producer IDs remain unresolved until trusted accepted producers exist.
- `FULL_ENGINE_VECTOR_CORPUS.json` carries 398 deterministic readiness/lock/replay vectors across Levels 1–100.
- `REFERENCE_RUNTIME_SEMANTICS.json` + `reference_progression_engine.py` freeze executable state-transition behavior for out-of-order facts, deterministic cascades, duplicate no-ops, milestone exactly-once publication and snapshot/restore.
- `materialize_progression_data.py` can generate both shipping-shaped JSON documents in memory now and run the real shipping validator. Repository writes remain fail-closed until T12 is activated, claimed with `@reservation:T12`, and exact binding proof passes.

## Required source contract

### `progression_architecture.gd`

Progression-domain authority only:

1. load and validate the shipping Level 1–100 progression datasets;
2. expose stable level, milestone, region-band and one-time event IDs;
3. evaluate prerequisites deterministically from published upstream state inputs;
4. expose current-level/next-objective/milestone query data without a control-heavy UI dependency;
5. emit idempotent progression-event intents rather than directly mutating T07/T08/T10/T11 systems;
6. reject missing/duplicate/out-of-range/cyclic/unreachable progression topology;
7. reject invalid purchase/VIP/premium-spend prerequisite inputs;
8. preserve deterministic replay/re-evaluation behavior;
9. expose stable identifiers/schema for later T14 persistence without implementing global save/versioning;
10. avoid full-world/full-graph rebuilds each frame.

### `progression_levels_v1.json`

Exactly one shipping record must exist for every integer Level 1–100. Each record contains fields equivalent to:

- `level`
- `level_id`
- `region_band_id`
- `prerequisite_level_ids`
- `required_fact_ids`
- `progression_effects`
- `visible_progression_hook_ids`
- `milestone_ids`
- `one_time_event_ids`

Validation rejects wrong schema/task identity, missing/duplicate levels, noncanonical level/completion/milestone IDs, wrong region bands, missing or forward prerequisite targets, unresolved required facts, cycles/unreachable records, duplicate/filler progression effects, unresolved milestone references and monetization/spend/energy-gated eligibility.

### Fact-slot binding layer

Shipping level topology never embeds external producer IDs directly.

- Level 1: `required_fact_ids = []` so the progression can begin intrinsically.
- Levels 2–100: exactly one matching T12-owned slot, `t12.fact.slot.NNN`.
- A separate binding index maps the stable T12 slot to an authoritative `fact_kind + source_task + source_id`.
- T10/T11 source IDs behind slots require exact activation-time binding proof.
- Later T32/T44–T52 content may remain `DEFERRED_LATER_OWNER`; the slot identity remains stable and its level stays locked until a trusted registration exists.
- T12 owns slot identity/eligibility interpretation only, never the upstream gameplay fact.

### `progression_bindings_v1.json`

Canonical runtime binding data for the 99 fact-gated levels:

- exactly one binding row for each `t12.fact.slot.002` through `t12.fact.slot.100`;
- each row declares `slot_id`, `fact_kind`, `source_task`, `source_id`, `resolution_state`, `evidence_ref`, and `idempotency_domain`;
- `RESOLVED` rows point only to accepted authoritative producer facts;
- `DEFERRED_LATER_OWNER` rows may remain unresolved only where the frozen slot contract permits a later content owner and must keep the level locked;
- exact T10/T11 source IDs require activation-time binding proof;
- no purchase/VIP/spend/energy signal may appear as a producer fact;
- T12 owns slot identity/mapping semantics, never the upstream gameplay authority.

### `progression_milestones_v1.json`

Each milestone/hook record contains fields equivalent to:

- `milestone_id`
- `level`
- `kind`
- `progression_hook_ids`
- `visible_change_required`
- `owner_task`

T12 may reserve hooks owned by later tasks but may not claim those later assets/features are implemented. Major progression milestones are targeted approximately every ten levels and visible progression hooks must support the product requirement for noticeable improvement at least about every three levels.

## Mandatory implementation matrix

### Topology/data tests

- exactly 100 unique shipping level records, Levels 1 through 100 with no gaps;
- stable unique level/milestone/region/event IDs;
- all prerequisites target valid level IDs;
- prerequisite graph is acyclic and every shipping level is reachable from Level 1;
- no mandatory mutually exclusive conditions create a dead progression path;
- every level has at least one practical progression effect or unlock category;
- visual-progression hook cadence meets the architecture contract;
- major-milestone cadence is approximately ten levels and explicitly reported;
- no purchase-history/VIP/premium-spend/energy-gate prerequisites exist.

### Runtime behavior tests

- identical accepted state + inputs produce identical level eligibility/output;
- repeated evaluation does not double-unlock or duplicate one-time events;
- stale/out-of-order progression state fails closed rather than silently skipping prerequisites;
- T07 contextual-control state is consumed only through its published interface;
- T08 resource/inventory truth is read only through published state and never directly mutated;
- T10 transform identities/status are referenced without direct debit/commit mutation;
- T11 camp-state identities/status are referenced without direct content spawn/mutation;
- current-level/next-objective/milestone queries remain bounded and do not rebuild the whole graph/world every frame.

### Integration tests after T11 approval

- exact accepted T10/T11 public IDs/interfaces reconcile with prepared T12 bindings and canonical progression_bindings_v1.json rows;
- T12 never writes T10/T11 transaction/content state directly;
- progression-driven transform/camp hooks remain exact-once through their upstream authorities;
- approved T01–T11 regression remains clean;
- T13 can consume progression context without T12 implementing adaptive difficulty;
- T14 can persist stable T12 identities later without T12 defining the global save format;
- T32/T44–T52 can consume region-band/hook contracts without T12 pre-authoring their content.

### Readability/capture evidence

Where player-facing progression presentation exists, capture:

- normal-level state;
- level eligible/complete transition;
- visible-progression-hook level;
- major-milestone state;
- duplicate/replay attempt proving one-time results are not duplicated;
- gameplay-scale current-level/next-objective readability;
- adaptive phone/tablet/foldable layouts where applicable;
- exact-source performance/query records.

## Acceptance dimensions by critic

- **C2 Technical / Visual Integrity:** progression state, event identity and any player-visible transitions remain internally consistent; no duplicated/contradictory state or presentation defects.
- **C3 Havenline Gameplay Identity:** progression reinforces the physical/simple-context loop rather than turning Havenline into a button-heavy RPG/4X/management game.
- **C4 Gameplay UX / Readability:** the player can understand current progress, next meaningful objective/unlock and milestone changes without clutter or hidden requirements.
- **C6 Performance:** load/validation/query behavior is bounded, cached appropriately and preserves headroom; no per-frame full progression/world rebuild.
- **C7 Progression / Difficulty:** progression rises meaningfully, avoids empty/boring stretches and impossible spikes, provides meaningful upgrades and preserves a clean boundary for T13's bounded spend-blind Challenge Director.

## Protected boundaries

Do not edit from the T12 builder branch unless an approved structured ChangeRequest authorizes it:

- T07 contextual-control runtime;
- T08 inventory/carrying runtime;
- T10 world-transform runtime/data;
- T11 camp-construction runtime/assets/data;
- T13 challenge/difficulty runtime/data;
- T14 global persistence/versioning;
- T33+ economy/monetization systems;
- T44–T52 authored region systems/assets;
- `HavenlineGodot/scripts/main.gd`;
- `HavenlineGodot/scripts/simulation.gd`;
- canonical shared registries owned by integration.

## Parallel-prep work allowed before T11 approval

Allowed now:

- freeze and refine T12 scope/task packet without changing shipping scope;
- keep the future disjoint ownership paths collision-free;
- maintain the Level 1–100 record/milestone/region/event schemas;
- maintain static graph/cadence/spend-blind validation rules;
- bind accepted T07/T08/T10 contracts and keep T11 public-contract assumptions explicitly provisional;
- prepare validation and candidate CI scaffolding;
- deterministically preauthor all 100 T12 level/slot/fact-slot/effect/hook/milestone/event identities in non-shipping blueprints;
- maintain the 99-slot binding-index template without inventing unfinished producer IDs;
- dry-run the activation-gated shipping data materializer in memory;
- execute the exhaustive 398-vector full Level 1–100 reference corpus;
- test that activation fails closed while T11 is unfinished;
- maintain an activation tool that refuses activation until all dependencies are approved/integrated;
- static collision/review against T07/T08/T10/T11/T13 and integration-only paths.

Not allowed now:

- claim T12 shipping implementation as `ASSIGNED` or `BUILDING_ISOLATED`;
- create/modify shipping T12 progression runtime/data or invoke materializer write mode before T12 is activated/claimed;
- edit active T11 runtime/content;
- implement T13/T14/T33+/T44–T52 scope early.

## Activation handoff

When T11 is integrated and marked APPROVED, run the T12 activation preflight against the exact new integration head. It must fail on stale base, unapproved dependency, stale T10/T11 owner, conflicting path reservation, missing T10/T11 completion record or prepared-interface drift. Reconcile exact accepted T10/T11 source IDs, populate the resolved binding evidence and binding-index rows, then rerun the authoring/slot/materializer dry-run gates. After a clean preflight, create the empty `havenline/T12-progression-architecture` branch from the exact activation integration SHA, stage `@reservation:T12` plus PREPARED workstream registration through the integration owner, and grant real `ASSIGNED` authority only through `v32_assignment_claim.py` with exact remote builder/integration tips. After that assignment governance commit is merged, synchronize the empty builder branch to the claim commit, run registry/candidate guards, and only then allow `materialize_progression_data.py --write-shipping` to seed the three shipping data files before the runtime builder/critic loop. Never use legacy `workstream.py claim --status ASSIGNED` for T12.

See `ACTIVATION_CHECKLIST.json`, `PREBUILD_CONTRACT.json`, `FROZEN_SCOPE.md`, `defect-ledger.json`, and `tools/havenline/task12/prepare_activation.py`.
