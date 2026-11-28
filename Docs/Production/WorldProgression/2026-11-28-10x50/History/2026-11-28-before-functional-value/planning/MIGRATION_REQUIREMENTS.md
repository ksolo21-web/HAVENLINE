# Migration requirements — current 10×50 progression

## Boundary

This ledger identifies work that must be performed on the actual selected gameplay foundation after ownership/source reconciliation. It is not an implementation receipt. The current package edits only its own planning directory. Existing task IDs, dependencies, owners, source commits and historical approvals remain intact.

The old T12 preparation material targets a one-hundred-level architecture and interfaces from the earlier project. The Build 13 audit explicitly requires binding T12 to the accepted successor interfaces. A blind search-and-replace from 100 to 500 would damage tests, score thresholds, saved identities and source evidence. Old count-specific proofs do not certify a new candidate.

## Required decisions and changes

| Area | Observed issue | Required migration/acceptance |
|---|---|---|
| Identity | Old records use one global integer `level` and `t12.level.NNN`. | Adopt a versioned world/local identity design; a derived ordinal is available for internal ordering. Choose UI display separately. Map every supported old save/receipt deterministically, retain a legacy-ID map and prove idempotent reload/rollback. No IDs are rewritten by this package. |
| Authored outcomes | Existing content contains 100 prior-layout outcomes; the structural blueprint likewise has 100 slots. | Author meaningful World 1 outcomes across all fifty levels. Reuse valid earlier ideas, but do not multiply old levels or declare replicated rows to be new content. Later worlds each require fifty useful outcomes before their own integration. |
| Region ranges | Old region bands are ten global levels each. | Use ten worlds with fifty local levels each, preserve world themes and content-owner tasks, and author actual milestone/connection prerequisites. Later updates remain unavailable until released. |
| Fact bindings | Old data validates 100 records and 99 bindings, with one intrinsic-ready opening record. | Version the schema and binding index. Determine cardinality from approved world-entry semantics; do not blindly replace 99 with 499. Keep real producer bindings and fail closed on unresolved required content. |
| Progression cadence | Old visible hooks and region exits use modulo-ten tests and end-band levels 10,20,…100. | Preserve useful visible progression; author a cadence suited to fifty local levels and actual asset changes. A world exit is no longer inferred from every tenth global level. Existing milestone ideas are inputs, not new unlock approvals. |
| Dynamic economy | Staged `dynamic_economy.gd::_band(world)` computes `clamp((level−1)/10,0,9)` and quotes record `progression_level`/`band`. | Separate world identity, local progression band and equipment tier. Preserve existing accepted quotes/catalog versions and exactly-once contributions. Test high local levels, later worlds, loss/rebuild and post-update quotes. |
| Difficulty and raids | Progression bands influence obtainable gear, warning/encounter and recovery context. | Re-author fifty-level local challenge without spend inputs or arbitrary quantity inflation. Preserve the full five-minute active-play warning, named camp, paused background state and feasible recovery. |
| Released-content gating | Old T62/T70 chain assumes every planned region participates before final release. | Define explicit World 1 release and later-update acceptance profiles with a documented dependency reconciliation. Do not delete dependencies or declare all70 tasks complete. Retain all applicable security, audio, fairness, reference and physical-device requirements. |
| Visual upgrades | World levels, equipment levels, purchased tiers, appearance variants and damaged states can be confused. | Bind each visible change to an actual upgrade contract. Preserve approved baselines, source scale, footprint, ports and routes. Numeric asset caps/unlock points remain unassigned unless explicitly sourced. |
| Vehicles/materials | Garage and truck, low fuel use, iron bars/sheet metal, coal/oil and meaningful processors extend the earlier opening design. | Integrate source-bound typed resources and capability-gated bills. Preserve unlimited cargo, paid repair/replacement, tank/cargo separation and outside-wreck loss. Resolve the two documented policy conflicts before coding them. |
| Persistence/cloud | Old outcome and purchase identities cross updates, quotes, casualties, assets and entitlements. | Prove old/current saves, account recovery, partial operations, multiple released-world versions, interruption and rollback without duplicate awards or lost paid value. |
| Performance/release | Fifty levels can increase late-World1 assets, routes, stock and worker load. | Measure representative completed World1 load for its release, then recertify impacted updates. Do not lower current native-4K/60 or visual-quality gates or count a concept sheet as proof. |

## Source-backed affected paths

The exact read-only source hashes are in `SOURCE_EVIDENCE.json`. These paths require versioned revision/reconciliation by their existing owners; listing them grants no new path ownership.

### Current plan and generated maps

- `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md`
- `Docs/Production/DEPENDENCY_GRAPH.json`
- `Docs/Production/TASK_SCOPE_OVERRIDES.json`
- `Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md`
- `Docs/Production/FORWARD_EXECUTION_PROFILES.json`
- `Docs/Production/V32_FORWARD_PREP_ROADMAP.json`
- `Docs/Production/COMPLETENESS_STANDARD.md`
- `Docs/Production/WHOLE_GAME_COMPLETENESS.json`
- `Docs/Production/GAMEPLAY_DEPTH_STANDARD.md`
- `Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json`
- `Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.json`
- `Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md`
- `Docs/Production/GameplayRules/2026-11-27/PROGRESSION_ECONOMY_GAPS.json`
- `Docs/Production/GameplayRules/2026-11-27/PROGRESSION_ECONOMY_GAPS.md`
- `Docs/Production/GameplayRules/2026-11-27/TASK_GAMEPLAY_RULES_T01_T80.json`
- `Docs/Production/GameplayRules/2026-11-27/TASK_GAMEPLAY_RULES_T01_T80.md`
- `Docs/Production/GameplayRules/2026-11-27/TASK_COMPLETENESS_T01_T80.json`
- `Docs/Production/GameplayRules/2026-11-27/TASK_COMPLETENESS_T01_T80.md`
- `Docs/Production/GameplayRules/2026-11-27/TASK_GAMEPLAY_DEPTH_T01_T80.json`
- `Docs/Production/GameplayRules/2026-11-27/TASK_GAMEPLAY_DEPTH_T01_T80.md`

The current working-tree `GameplayRules/` documents are staged source bytes; their surrounding parent commit does not imply those files are published. Preserve dated earlier audit/Review snapshots. Update authoritative generators and regenerate their current crosswalks together instead of manually editing one table while leaving its machine-readable source stale.

### T12 preparation, schemas and downstream contracts

- `Docs/Production/T12/LEVEL_1_100_MATRIX.json`
- `Docs/Production/T12/AUTHORING_BLUEPRINT.json`
- `Docs/Production/T12/BINDING_SLOT_CATALOG.json`
- `Docs/Production/T12/FACT_SLOT_BINDING_INDEX_TEMPLATE.json`
- `Docs/Production/T12/PROGRESSION_DATA_SCHEMA.json`
- `Docs/Production/T12/RUNTIME_INTERFACE_CONTRACT.json`
- `Docs/Production/T12/DOWNSTREAM_CONSUMER_CONTRACT.json`
- `Docs/Production/T12/PREBUILD_CONTRACT.json`
- `Docs/Production/T12/ACCEPTANCE_TRACEABILITY.json`
- `Docs/Production/T12/LEVEL_CADENCE_BLUEPRINT.md`
- `Docs/Production/T12/FROZEN_SCOPE.md`
- `Docs/Production/T12/TASK_PACKET.md`
- `Docs/Production/T13/T12_CONSUMER_BINDING.json`

Keep the original `LEVEL_1_100_MATRIX.json`, old schema and count-specific evidence recoverable. Introduce a versioned replacement or an explicit migration rather than pretending the original receipt covered five hundred positions. Update evidence templates/test-vector fixtures only for the new candidate; preserve old proof files.

### Count/range-sensitive implementations and validators

- `tools/havenline/task12/validate_level_matrix.py`
- `tools/havenline/task12/validate_progression_contract.py`
- `tools/havenline/task12/validate_authoring_blueprint.py`
- `tools/havenline/task12/validate_fact_slot_binding_index.py`
- `tools/havenline/task12/validate_downstream_contract.py`
- `tools/havenline/task12/validate_runtime_interface.py`
- `tools/havenline/task12/validate_data_schema.py`
- `tools/havenline/task12/validate_traceability.py`
- `tools/havenline/task12/reference_progression_oracle.py`
- `tools/havenline/task12/materialize_progression_data.py`
- `tools/havenline/task12/prepare_activation.py`
- `tools/havenline/task12/fuzz_progression_contract.py`
- `tools/havenline/production/completeness.py`
- `tools/havenline/gameplay_rules/dynamic_economy.gd`

The T12 files contain explicit100/99 checks, ten-level range tuples, milestone lists and/or old semantic guard text. `tools/havenline/production/completeness.py` requires100 ordered unique outcomes and ten `[start,start+9]` region ranges. The staged economy `_band` calculation is a demonstrated semantic risk for both local and global numbering. Tests and materializers must be updated in a coherent versioned change; unrelated constants such as critic scores, test iterations or quantity limits must remain untouched.

## Mandatory migration evidence before gameplay approval

1. Every released world has exactly local Levels1–50, valid unique identities, reachable prerequisites and a useful authored payoff per level.
2. World1 is fully playable without unpublished-world assets/resources/vehicles; the sandbox continues after its local Level50.
3. Earlier saves, earned levels, receipts, typed stock, partial quotes, companions and entitlements survive one migration and repeated restore unchanged in value.
4. Each newly introduced local-level/region/asset-tier boundary chooses attainable demand and bills; accepted terms do not reprice when the player advances or updates.
5. No upgrade or recovery requires its own unavailable output or an unreleased world; losing the furnace, vehicle and workers still leaves an ordinary recovery path.
6. Every required appearance stage has selected render evidence plus native geometry/port/collision/use-state review before implementation approval. Full actions, audio and device proof remain separate.
7. World1 release, later-world update and final500-position campaign evidence are separately named and scoped. No historical/full-campaign approval is synthesized.
8. The unresolved warehouse-deposit and general in-camp blade-policy conflict is explicitly resolved from owner authority before implementation; the render work does not decide it.

## Historical material to preserve

Preserve `Docs/Production/Archive/`, `Docs/RepositoryArchive/`, all prior `Review/`, `evidence/`, freeze/publication receipts and exact committed source snapshots, the original100 authored outcomes, accepted task status/owner/dependency records, all selected/rejected renders and their original meanings. Add supersession links and new evidence instead of rewriting history. T71–T80 remain source gaps, not available numbers for filler tasks.
