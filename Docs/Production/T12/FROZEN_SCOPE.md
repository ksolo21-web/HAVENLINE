# T12 frozen scope — Level 1–100 progression architecture

## Required outcome

Define the deterministic, data-driven Level 1–100 progression architecture that later content, difficulty, economy, persistence and region tasks can consume without each inventing their own progression rules. T12 owns level identity, prerequisite/milestone topology, progression-event contracts, visual-progression cadence metadata and stable bindings to already-approved/accepted gameplay systems.

T12 consumes the approved T07 Simple Control & Context Director, T08 visible inventory/physical carrying, T10 World Transformation Framework and T11 camp construction/visual upgrade system. It must not rewrite those systems. T13 owns adaptive difficulty/Challenge Director behavior, T14 owns save-state/versioning, T33+ own economy/monetization, and T44–T52 own authored region content.

The permanent Havenline product contract remains authoritative: launch progression spans Level 1–100 across a connected world; every level must have a practical progression effect; noticeable visual improvement is targeted at least about every three levels; major milestones occur approximately every ten levels; the game remains realistically completable at $0 and has no energy wall or purchase-gated progression.

## Mandatory requirement IDs

- **T12-R01 — Stable Level 1–100 identity.** Shipping progression defines exactly one stable record for each integer level 1 through 100, with deterministic canonical level IDs, region-band identity, prerequisite IDs, required authoritative-fact IDs, milestone references and canonical completion-event identity. Duplicate, missing, out-of-range, schema-drifted or cyclic level topology fails closed.
- **T12-R02 — Practical progression every level.** Every shipping level record must declare at least one meaningful progression effect or unlock category. Empty/placeholder levels that advance only a counter are forbidden.
- **T12-R03 — Visual-progression cadence contract.** The architecture records visible-world/progression hooks so later authored content can produce noticeable visual improvement at least about every three levels and a major milestone approximately every ten levels. T12 defines and validates the cadence contract; later owner tasks author the region/content assets.
- **T12-R04 — Connected-world region slots without pre-authoring later regions.** The architecture reserves the frozen opening band around Levels 1–10 and the later connected-region bands consumed by T44–T52 through Level 100, using stable region/progression IDs. T12 does not build forest/desert/underwater/sky/volcanic/swamp/ruins/underground/alien region content.
- **T12-R05 — Existing-system bindings only.** Progression events may reference published T07/T08/T10/T11 interfaces and stable IDs, but T12 may not mutate contextual controls, inventory/carrying conservation, world-transform transaction semantics or camp construction state directly.
- **T12-R06 — Visible upgrade/world-change truth.** Any progression record that advances through a T10/T11 world or camp transformation must bind to a real transform/camp-state identity and must not represent a hidden stat-only substitute for a required visible upgrade.
- **T12-R07 — Spend-blind progression topology.** Level eligibility/prerequisites may not read purchase history, VIP status, premium spend or monetization signals. T12 exposes no pay-to-unlock or energy-wall path. Economy tuning remains T33+; adaptive difficulty remains T13.
- **T12-R08 — Deterministic progression state contract.** Given the same accepted upstream state and progression inputs, level/milestone eligibility and emitted progression events are deterministic and idempotent. Repeated evaluation cannot double-unlock, skip prerequisites or emit duplicate one-time progression events.
- **T12-R09 — Recovery-compatible identifiers.** Level, milestone, region-band, unlock and event IDs are stable so T14 can persist/recover them without redefining T12 semantics. Canonical completion events use `t12.event.level.NNN.completed` and default major milestones use `t12.milestone.NNN`. T12 does not implement the global save/versioning layer.
- **T12-R10 — No impossible progression graph.** Static validation rejects cycles, missing prerequisite targets, forward references that create dead ends, mutually exclusive mandatory requirements, unreachable shipping levels and any path that prevents a valid Level 1→100 progression chain.
- **T12-R11 — Clear progression/readability contract.** Player-facing progression events expose concise data for current level, next meaningful objective/unlock and major milestone state without requiring a control-heavy RPG tree or management screen. Any UI added later must preserve T07 simple-control philosophy.
- **T12-R12 — Performance-bounded evaluation.** Progression lookup/evaluation is data-driven and bounded; it must not scan or rebuild the full world every frame. Static validation and milestone queries preserve performance headroom.
- **T12-R13 — Later-owner boundaries.** T12 does not implement T13 Challenge Director tuning, T14 persistence/migration, T15+ customer/production/combat systems, T33+ economy/monetization, T44–T52 region art/gameplay, or T62 full Level 1–100 acceptance.
- **T12-R14 — Integration-safe shared wiring.** T12 builder owns only its disjoint progression files. Shared `main.gd`, `simulation.gd`, canonical governance registries and upstream task files remain integration-owner/upstream-owner controlled. Missing upstream hooks require a structured ChangeRequest rather than foreign-path edits.
- **T12-R15 — Dependency truth.** T12 production implementation may not enter `ASSIGNED`/`BUILDING_ISOLATED` until T07, T08, T10 and T11 are all `APPROVED`, with T10/T11 integrated on the authoritative integration branch. Governance packet/tooling preparation may complete while remaining dependencies are unfinished; at the current checkpoint T10 is APPROVED/integrated and T11 remains the active unfinished dependency.
- **T12-R16 — Acceptance gate.** Required critics are C2/C3/C4/C6/C7 exactly as registered. Every mandatory dimension must be strictly greater than 9.0 unrounded, target 10/10; all applicable G1–G14 gates and impacted approved-task regression must pass with zero unresolved mandatory defects.

## Explicit exclusions

- No T13 adaptive-difficulty/Challenge Director implementation or tuning.
- No T14 save/versioning/migration implementation.
- No shipping economy prices, premium currency, VIP, store or purchase gates.
- No authored T44–T52 biome/region content.
- No customer, fishing/food, combat, defense, companion or LiveOps implementation.
- No direct edits to T07/T08/T10/T11 runtime ownership.
- No unrestricted skill tree, button-heavy progression menu or mandatory manual inventory management.
- No empty filler levels, hidden paywall prerequisites or energy gating.

## Planned ownership reservation

The T12 isolated builder will own only the following disjoint paths once activation is legal:

- `HavenlineGodot/scripts/progression_architecture.gd`
- `HavenlineGodot/data/progression_levels_v1.json`
- `HavenlineGodot/data/progression_milestones_v1.json`
- `HavenlineGodot/tests/test_task12_progression_architecture.gd`
- `HavenlineGodot/tests/test_task12_integration.gd`
- `HavenlineGodot/tests/capture_task12_progression.gd`

The preparation/acceptance surface is intentionally **not** builder-owned after activation: `Docs/Production/T12/**`, `tools/havenline/task12/**`, and T12 preparation workflows are frozen baseline inputs. If a defect is later found in those rules/tools, stop the shipping candidate and reopen pre-activation repair rather than letting the candidate rewrite its own acceptance contract.

T12 may reference but not mutate T07/T08/T10/T11 source/runtime. Shared shipping wiring (`main.gd`, `simulation.gd`, canonical registries) remains integration-owner work.

## Required acceptance evidence after activation

- Exact post-T11 integration base, candidate hash and authorized changed-file manifest.
- Machine-readable manifest proving exactly 100 unique ordered shipping level records and stable milestone/region/event IDs.
- Static graph proof: no missing/duplicate/out-of-range levels, no cycles, no unreachable shipping level, no broken prerequisite target and at least one valid Level 1→100 chain.
- Per-level meaningful-effect/unlock coverage; no counter-only filler level.
- Visual-progression cadence report showing the architecture supplies visible progression hooks at the required practical cadence and major milestones approximately every ten levels without pretending later region assets already exist.
- Binding tests for T07/T08/T10/T11 public interfaces/IDs, including exact-once/idempotent progression event behavior and no upstream state mutation.
- Spend-blind checks proving progression evaluation cannot consume purchase/VIP/premium-spend signals and contains no energy-wall/pay-to-unlock prerequisite.
- Deterministic replay/re-evaluation proof: no duplicate one-time unlocks, skipped prerequisites or divergent output from identical accepted state.
- T14-ready stable identifier/schema contract without implementing global persistence.
- Gameplay/readability evidence for current-level/next-objective/milestone signaling where player-facing presentation exists, across adaptive layouts when applicable.
- Performance record for load/validation/query costs and proof that progression does not perform full-world/full-graph rebuilds every frame.
- Full impacted T01–T11 regression after integration.
- Independent C2/C3/C4/C7 review plus quantitative C6; every mandatory dimension strictly >9.0 unrounded, target 10/10.
