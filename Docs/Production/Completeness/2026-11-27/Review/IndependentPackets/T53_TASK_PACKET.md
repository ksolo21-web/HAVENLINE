# Havenline frozen task packet — T53

Generated: 2026-11-27T12:46:06.969672+00:00

## Identity
- Task ID: T53
- Task name: Transportation and inter-region continuity
- Workstream ID: UNASSIGNED
- Owner: UNASSIGNED
- Isolated branch: UNASSIGNED
- Exact base integration commit: UNASSIGNED

## Dependencies
Required APPROVED upstream tasks: T43, T44, T45, T46, T47, T48, T49, T50, T51, T52

## Owned paths
- UNASSIGNED

## Protected paths
- resolve from PATH_OWNERSHIP.json

## Acceptance gates
- G1: REQUIRED unless this packet records explicit N/A rationale.
- G2: REQUIRED unless this packet records explicit N/A rationale.
- G3: REQUIRED unless this packet records explicit N/A rationale.
- G4: REQUIRED unless this packet records explicit N/A rationale.
- G5: REQUIRED unless this packet records explicit N/A rationale.
- G6: REQUIRED unless this packet records explicit N/A rationale.
- G7: REQUIRED unless this packet records explicit N/A rationale.
- G8: REQUIRED unless this packet records explicit N/A rationale.
- G9: REQUIRED unless this packet records explicit N/A rationale.
- G10: REQUIRED unless this packet records explicit N/A rationale.
- G11: REQUIRED unless this packet records explicit N/A rationale.
- G12: REQUIRED unless this packet records explicit N/A rationale.
- G13: REQUIRED unless this packet records explicit N/A rationale.
- G14: REQUIRED unless this packet records explicit N/A rationale.

## Required critics and executable safeguards
- **C1 — Reference Fidelity Critic**: `tools/havenline/production/critic_harness.py validate-raw --critic C1`; dimensions: reference_fidelity, visual_language, cross_view_consistency.
  - current evidence contract: `Docs/Production/EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`
  - execution scope: Validates evidence retained by an actual separate agent/model review; this command does not perform or invent the visual review.
- **C2 — Technical / Visual Integrity Critic**: `tools/havenline/production/critic_harness.py validate-raw --critic C2`; dimensions: geometry_contact, clipping_seams, intentional_gap_integrity, cross_view_integrity.
  - current evidence contract: `Docs/Production/EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`
  - execution scope: Validates evidence retained by an actual separate agent/model review; this command does not perform or invent the visual review.
- **C3 — Havenline Gameplay Identity Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: havenline_identity, simple_context_controls, physical_core_loop, complexity_discipline, world_response_readability.
  - evidence categories: gameplay_state, control_state, loop_evidence
- **C4 — Gameplay UX / Readability Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: interactable_clarity, danger_clarity, collection_feedback, resource_destination, world_change_clarity, next_action_clarity.
  - evidence categories: gameplay_state, feedback_state
- **C6 — Performance Critic**: `tools/havenline/production/critic_harness.py ingest-performance-review`; dimensions: frame_time, draw_calls, geometry, texture_memory, shader_cost, physics, animation, population, thermal_risk.
  - current evidence contract: `Docs/Production/EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`
  - execution scope: Current final evidence combines unchanged independent scores and exact hash-bound measurements. The measurement gate alone cannot approve the critic.
- **C7 — Progression / Difficulty Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: difficulty_growth, challenge_variety, spike_control, pacing, upgrade_meaning, director_bounds.
  - deterministic supplement: `tools/havenline/production/domain_safeguard_gate.py progression`
  - evidence categories: progression_simulation, difficulty_curve, upgrade_curve

## Resource / tool / actor / animation contract
- N/A for this task under the current forward policy. Do not expand frozen scope merely because the contract exists.

## Registered forward contracts
- none registered for this task.

## Forward execution profile — machine resolved
- Standard: `Docs/Production/FORWARD_EXECUTION_STANDARD.md`
- Resolver: `python3 tools/havenline/production/forward_execution.py plan T53`
- Archetype: `progression_world`
- Execution mode: `build`
- Dependency states: `T43=LOCKED, T44=LOCKED, T45=LOCKED, T46=LOCKED, T47=LOCKED, T48=LOCKED, T49=LOCKED, T50=LOCKED, T51=LOCKED, T52=LOCKED`
- Dependencies currently approved: `false`
- Canonical packet currently present: `false`
- Activation ready now: `false`
- Early sentinel: inter-region route reachability, transition/save continuity, stranded-state recovery and transport performance
- Ordered fail-fast gates:
  1. `scope_dependency`
  2. `ownership`
  3. `reference_lock`
  4. `source_contract`
  5. `focused_unit`
  6. `task_sentinel`
  7. `progression_sim`
  8. `save_matrix`
  9. `device_matrix`
  10. `impacted_regression`
  11. `performance`
  12. `visual_evidence`
  13. `critic_review`
  14. `integration`
  15. `post_integration_regression`
  16. `closeout`
- Terminal-failure disposition: C0 -> bounded builder repair plan
- Exact-SHA rule: finish the candidate already under review; newer candidates queue. Do not use `cancel-in-progress: true` for task candidate review.
- Do not run expensive downstream evidence after an earlier required gate fails. Preserve the exact failure and invoke C0.

## Production Architecture V3 — machine resolved
- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V3.md`
- V3 readiness: `python3 tools/havenline/production/architecture_v3.py readiness T53`
- Feasibility state: `PREP_ONLY`
- Runtime activation allowed now: `false`
- Capability blockers: android_build_toolchain, c0_advisor, independent_critic_runtime
- Scheduler class: `PREP_ONLY`; deterministic priority score: `93` (scheduling heuristic only, never an acceptance score).
- Produces versioned contracts: region_transition
- Consumes versioned contracts: inventory_transfer, harvest_resource_identity, progression_state, challenge_director_input, persistence_schema, population_actor
- Before runtime activation: resolve all required capabilities; unknown external/hardware prerequisites are not READY.
- Before integration: run `synthetic_merge_forecast.py` against the current integration head and validate any affected shared contract change.
- Gate proof reuse is allowed only through `gate_fingerprint.py`; exact-source-only gates remain fresh and failed results can never be reused as PASS.
- C0 must query `FAILURE_INTELLIGENCE.json` before repair; historical matches are advisory and require confirmation from current evidence.
- **DO NOT start runtime implementation from this packet yet.** Preparation is allowed, but the recorded V3 activation blocker(s) must clear first.

## Production Architecture V3.1 — machine resolved
- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V31_STANDARD.md`
- V3.1 readiness: `python3 tools/havenline/production/architecture_v31.py readiness T53`
- Canonical task-state snapshot: `python3 tools/havenline/production/task_state_snapshot.py T53`
- Every terminal task validation must preserve `factory-observation.json` generated by `tools/havenline/production/factory_observer.py` from the exact GitHub run/jobs/artifacts. C0 does this automatically for terminal failures; success/closeout workflows must do the same before APPROVED.
- Before T10+ approval, run `python3 tools/havenline/production/factory_closeout_gate.py --task T53 --candidate <SHA> --observation <factory-observation.json>`; this gate validates the observation but never grants approval by itself.
- Factory observation produces queue/run/gate telemetry, exact-environment flake observations, the derived task-state snapshot, and any exact-source runtime dependency traces. It is evidence, never a second lifecycle authority.
- Persistent flake history may change diagnosis/retry routing only; a mandatory flaky gate still blocks approval. If runner provenance is missing or ambiguous, flake observations are suppressed rather than guessed.
- Pipeline telemetry records queue/run/gate cost for factory optimization; it cannot change quality thresholds.
- Environment-sensitive proof reuse requires matching runner/toolchain provenance under `CI_TOOLCHAIN_LOCK.json`.
- Approval closeout must satisfy `EVIDENCE_RETENTION_POLICY.json`; artifact expiry cannot erase approval provenance.
- Runtime-observed dependencies are additive only and may add regression suites, never remove static mandatory coverage.
- Mutation canaries must pass before architecture closeout.
- If this task or a consumed contract is reopened, run `python3 tools/havenline/production/proof_invalidation.py task T53` or the affected contract form before reusing downstream proof.
- V3.1 runtime activation allowed now: `false`
- **DO NOT start runtime implementation from this packet yet.** V3 capabilities may be ready, but V3.1 lifecycle, ownership, or canonical-state blockers must clear first.

## Production Architecture V3.2 — machine resolved
- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V32_STANDARD.md`
- V3.2 readiness: `python3 tools/havenline/production/architecture_v32.py readiness T53`
- Parallel-preparation class: `PREP_NOW`; safe work: packet, frozen_scope, reference_lock, fixtures, test_scaffold, schema, asset_audit, capability_check, critic_scaffold, performance_allocation, save_security_cases
- Packet-local ASSIGNED graduation result (remote lineage proof is resolved only at activation): `false`
- Timeout-safe stage shards: `12`; critic fan-out lanes: `6`
- Before ASSIGNED: prove exact control-plane lineage with `python3 tools/havenline/production/task_graduation_gate.py T53 --target ASSIGNED --builder-head <EXACT_BUILDER_HEAD> --integration-head <EXACT_CURRENT_INTEGRATION_HEAD>`.
- Governance-only drift may preserve frozen scope/prepared runtime work, but it never waives control-plane synchronization. `control_plane_lineage.py` must show the integration head is an ancestor of the builder head.
- Claim ASSIGNED only through `python3 tools/havenline/production/v32_assignment_claim.py T53 --owner <OWNER> --branch <BRANCH> --base <EXACT_RECONCILED_INTEGRATION_HEAD> --owned-alias <ALIAS> --builder-head <EXACT_BUILDER_HEAD> --integration-head <EXACT_CURRENT_INTEGRATION_HEAD>`; it verifies the actual remote branch tips and records the assignment binding.
- Before BUILDING_ISOLATED: create `Docs/Production/T53/GRADUATION.json` and pass `python3 tools/havenline/production/task_graduation_gate.py T53 --target BUILDING_ISOLATED`.
- Initialize/update `execution_checkpoint.py`; on timeout preserve `INFRASTRUCTURE_FAILURE` and resume the same exact SHA/stage instead of restarting the task.
- Run `python3 tools/havenline/production/timeout_stage_plan.py T53`; do not combine unrelated expensive stages into one uncheckpointed job.
- Task workflows must call `havenline-v32-task-preflight.yml` as the shared control plane: `mode: preflight` before expensive build work, `mode: review` after source-bound specialist evidence exists, and `mode: failure` under `if: failure()` for task-local failures.
- The shared control plane owns exact builder/candidate/integration lineage binding, graduation, remote branch budget, gate-fingerprint decisions, synthetic-merge/contract checks, checkpoint resume validation, critic-package preflight, specialist fan-out, and C0 routing. C1/C2 and deterministic C6/C9 remain in their required task-specific lanes.
- If three blockers accumulate on one frozen candidate, `blocker_family_gate.py` requires causal-family reconciliation before another candidate.
- Use `critic_invalidation.py` to preserve unchanged same-SHA critic passes; a source-SHA change still requires fresh exact-source review where V3/V3.1 require it.
- Rolling prevention canaries: `python3 tools/havenline/production/rolling_canary.py requirements T53`.
- Record cumulative workload pressure with `performance_ledger.py`; C6 quality scores cannot waive performance budgets or reserved headroom.
- After a deterministic/source-bound gate PASS, stage a content-addressed proof record with `gate_result_recorder.py proposal`; CI cannot promote it. Only the integration owner may apply a verified proposal into `GATE_RESULT_INDEX.json`.
- C0 automatically stages unverified failure-learning proposals. They remain advisory/non-authoritative until a verified post-repair proof plus explicit integration-owner disposition promotes one into `FAILURE_INTELLIGENCE.json`.
- Parallel preparation of later tasks is encouraged only inside GREEN/YELLOW boundaries; it never grants integration or approval.

## Whole-game stakes, useful companions and resource value

Forward requirements: `Docs/Production/GAMEPLAY_DEPTH_STANDARD.md` and `GAMEPLAY_DEPTH_CONTRACT.json`. This addendum does not reopen frozen historical scope, change dependencies/ownership, activate a task, or certify runtime behavior. Use the existing scope/change process for a changed approved component. Owner/consumer labels are responsibilities, not new dependency edges.

- **GD01 — Readable stakes and bounded recovery (consumer)**: Define each threat warning, cause, consequence, exposure limit, counterplay, recovery, grace/repeat/offline behavior and save semantics. Select the proposed loss policy explicitly; never present it as observed footage or implemented behavior. Evidence: Threat/consequence/recovery table; Actual failure and repeated-failure playthrough; Free recovery from combined shortages; Muted/reduced-motion cue review.
- **GD02 — Persistent loss, cargo and recovery integrity (consumer)**: Preserve authoritative cargo, purchase and recovery receipts through cancellation, defeat if designed, app suspension, crash, reconnect and migration; no duplicated payout/debit or repeated committed penalty. Evidence: Save/reload at each transaction/recovery phase; Replay and interruption conservation tests; Current exact-source custody traces.
- **GD03 — Complete survivor assistance (consumer)**: Provide a trained/equipped survivor path for every physical human task family in ACTORS_MOTION_REQUIREMENTS.json. Specialization changes competence and preference; missing capabilities cannot silently become permanent exclusions. Evidence: Ten-family actor/action coverage; Complete work-to-destination scenarios; Region/equipment eligibility and explicit exceptions; Role-appropriate full motion.
- **GD05 — Useful large mixed survivor loads (consumer)**: Use shared typed custody and large useful mixed carrying with readable stacks. Preserve unlimited logical player inventory; explicitly reconcile finite/upgradable worker capacity before choosing its values. Evidence: Capacity-policy decision with real trip/throughput evidence; Partial/full multi-type transfer conservation; Loaded turns and two-gate clearance; Upgrade and visual stack compression proof.
- **GD07 — Distinct useful seven-companion roster (consumer)**: Preserve seven species and existing authored capabilities; prove a distinct useful normal-play role per pet with meaningful player benefit and complete species motion. Recommended role emphases remain explicit authoring choices. Evidence: Individual species-usefulness scenario; Controlled comparison with idle companion; Mixed human/pet team scenario; Distinct-view full work/attack cycles.
- **GD09 — Full state/action/transition animation (consumer)**: Cover the twelve animation families, complete loops, transitions, contact, interruption, blocked/full/empty and resume states. Use justified static/shared dispositions where appropriate; no generic placeholder masquerades as finished action. Evidence: Action/state inventory linked to actual clips/mechanisms; Real-time and slow playback from distinct meaningful views; Feet/toes/knees/hands/paws/tails/wings/tool/cargo contact; State-to-authoritative-event alignment.
- **GD10 — Meaningful machinery and logistics motion (owner)**: Machines, belts, storage, defenses and vehicles visibly perform their actual function across idle/input/start/run/output/empty/full/blocked/damaged if designed/restart states. Preserve typed custody and real output transactions. Evidence: End-to-end input-to-output-to-destination capture; Backpressure/empty input/repair/reconnect scenario; No cosmetic-only production; Contact and entry/exit consistency.
- **GD12 — Action-complete audio and accessible feedback (consumer)**: Feature owners emit truthful event phases; T54 freezes cue/mix/music/ambience or justified silence and listening evidence for each applicable event, variant and interruption. Critical information remains readable muted/reduced motion. Evidence: Per-event sound/music disposition; Actual listening under busy mixed activity; No success sound on denied/replayed transaction; Priority/concurrency/accessibility evidence.
- **GD13 — Every shipped material has a meaningful purpose (consumer)**: Each introducing feature freezes acquisition, actual identity/alias, processing, primary use, payoff, demand, availability/cost, custody and surplus/retirement. T33 later validates the combined economy; it is not an added circular prerequisite to earlier producers. Evidence: Resource-value ledger and actual ID bindings; One demonstrable useful outcome per shipped ID; Recipe/source/sink/phase coverage; No undeclared concept-to-item conversion.
- **GD14 — Resource and render reconciliation (consumer)**: Reconcile six canonical IDs, current-foundation IDs, thirteen base and twenty expansion render rows. Keep variants, containers and unselected concepts separate from canonical economy IDs; preserve all assets and decisions. Evidence: Exact source/render commit/path/hash inventory; Explicit alias/use/defer/exclude disposition per concept; Current foundation coal/slate/metal, processed-output and cash gaps resolved by owner evidence; No recipe/drop/price inferred from a still.
- **GD16 — Worthwhile collection and recoverable fair progression (consumer)**: Prove early/mid/late and low-resource routes at realistic free-player throughput; avoid circular inputs, stranded currencies, useless active inventory, deliberate drudgery or energy/pay recovery walls. A purposeful single-use quest item is valid with an explicit lifecycle. Evidence: Reachable progression dependency/recipe simulation; Novice/returning/optimized and repeated-failure sessions; Surplus/retirement and capped storage/worker-destination cases; preserve unlimited logical player inventory; No infinite conversion or intentional-failure reward loop.
- **GD17 — Integrated busy-shift and device proof (consumer)**: Measure concurrent working humans, pets, enemies, machines and deliveries with interruption/recovery on target devices. Visual/decision scaling preserves gameplay truth and readable attacks; planning checks cannot establish FPS or population capacity. Evidence: AC10 device/population scenario; Sustained source-bound CPU/GPU/memory and frame evidence; Busy-cycle and muted/reduced-motion review; No full-cost path recomputation for every idle actor.

Task-specific actor/motion details:

- Human logistics and companion compatibility with transport/routes/region transitions; no living actors on industrial belts.

Use the complete source-bound resource ledger and actor scenarios under `Docs/Production/GameplayDepth/2026-11-27/`. The introducing task freezes a useful resource contract before its own integration; T33 later reconciles it. Each pet proves standalone usefulness before T31 integration. All future play scenarios remain untested by this planning audit. Preserve the existing >=9.9 and stronger exact-10 reference rules.

## Current whole-game decisions and gap closure

Read `Docs/Production/COMPLETENESS_STANDARD.md`, `WHOLE_GAME_COMPLETENESS.json` and `CURRENT_GAMEPLAY_SOURCE.json`. The CD choices supersede the earlier D01–D05 open behavior wording; numeric tuning and actual game evidence remain open. These responsibilities are not new dependency edges or task activation, and preserve frozen historical scope.

- **CG02 — All-task survivors and large mixed carrying (consumer):** Use player-like unlimited logical cargo and all ordinary physical job families, including all authorized plots/conveyors and ordinary-cash buying; retain budgets and equipment truth. Required evidence: All ten human task families demonstrated.; Large mixed load conserved through service/payment/combat/reload.; No basic-AI paygate or autonomous premium spend.
- **CG05 — Useful active team and reserve population (consumer):** Three field pets and two survivor escorts, with useful camp assignments and conserved offscreen active-session work. Ownership, deployment and injury are separate states. Required evidence: Swap at safe camp with cargo/injury/recovery preserved.; No cooldown reset, cloned actor or invented unseen combat rewards.; Actual population census and sustained busy-scene proof.
- **CG07 — Ten regions and credible animal access (owner):** Bind each region to a concrete production/traversal payoff and supported actor routes; unsuitable pet environments use useful safe assignments. Required evidence: Ten-band goals and actor travel/work/attack applicability.; Free return, no stranded cargo, no underwater owl or flying quadruped.
- **CG09 — Materials, money and real demand (consumer):** Bind actual raw/product/currency IDs to named uses; coal/slate/metal/planks/blocks and cash receive real spending/processing sinks. Concepts have explicit selected/alias/reserve roles. Required evidence: Useful source-to-use-to-payoff loop for every shipped ID.; One ordinary currency and one primary premium currency; custody locations are not wallets.; No fake aliases or recipe facts inferred from art.; Ordinary cash conservation includes committed spending: cash sources equal till+pocket+house+committed outflow, so a new debit cannot reappear in a derived till balance.
- **CG13 — Smart actors under congestion and change (consumer):** Reserve jobs and approach lanes; bound retries, detect unreachable/depleted/full targets, keep priorities stable and explain a useful fallback. Navigation/avoidance alone does not satisfy smart behavior. Required evidence: Two workers competing for final resources/payment.; Narrow gate, moving target, broken route, full store, changed goal and path recovery.; No actor stuck idle when valid authorized work exists, no target thrashing or unbounded per-frame path replanning.
- **CG14 — Complete action, machine and sound states (owner):** Prove complete start/work/contact/success/miss/blocked/empty/full/cancel/recovery transitions for every applicable actor, machine, tool and transport. Use actual clip/contact/audio bindings. Required evidence: Full cycles and transitions from meaningful angles, feet/toes/knees, attachments and clipping.; Actual sound listening in busy play; mute/reduced-motion equivalents.; No success sound or transfer effect for denied/replayed transaction.
- **CG15 — Reference and render fidelity at every use state (consumer):** Use pinned selected GitHub references with explicit observed/authored/inferred distinctions. Current candidate must meet>=9.9 reference dimensions and every stronger exact10 visual rule; historical static scores do not pass runtime. Required evidence: Exact image/model/rig/scene/clip/source identity.; Actual matched-camera play and full motion evidence; no average hides a failed area.; Missing source or tiny unidentified figure stays unresolved rather than guessed.
- **CG16 — One unambiguous gameplay continuation source (consumer):** Use CURRENT_GAMEPLAY_SOURCE.json and corrected root entrypoints: newer Codex field project; main/alfred commands are explicitly historical. Resolve actual live head and owner before edits. Required evidence: Entry-point guidance agrees on branch/project/scene.; No runtime merge, branch reassignment or historical receipt rewrite.
- **CG18 — Accessibility across actual play states (consumer):** Apply existing readable text/contrast/non-color cues/touch size/reduced motion/subtitles/input preferences to threats, helper intent, resource purpose, care, payments and event expiry. Persist preferences. Required evidence: First-use/busy-camp/denied/resume states readable muted and reduced-motion.; Quality/orientation/fold changes preserve hit targets and input release; no hidden critical cue.

Applicable selected decisions: CD03, CD04, CD05, CD07, CD08, CD10.
Use the 100 authored outcomes, seven attack/specialty/render bindings and ten transaction boundaries in `Completeness/2026-11-27/`. All gameplay scenarios remain unrun by this audit. Current reference >=9.9 and stronger exact-10 visual requirements still apply.


## Current score policy
Every mandatory dimension >= 9.5 unrounded; reference-sensitive dimensions >= 9.9; C1,C2,C3,C4,C5,C11 every mandatory dimension exactly 10.0; no averaging or rounding; complete evidence; zero mandatory defects


## Score rule
Use Docs/Production/REFERENCE_ACCEPTANCE_POLICY.json and REFERENCE_ACCEPTANCE_STANDARD.md.
Final reference-sensitive dimensions >=9.9 unrounded; preserve all stronger exact-10 visual gates.
Other mandatory specialist dimensions >=9.5. A reference-sensitive 9.5 is interim only.
No averaging, rounding, missing evidence or unresolved mandatory defects. Freeze the input manifest's
reference_sensitive_dimensions per critic before review; the reviewer cannot omit them.

## Critic independence
C1/C2 and every specialist critic marked independent-model-required must run in a separate review job/runtime. A builder prompt, persona swap, or self-review never qualifies. If the zero-cost independent runtime is unavailable, construction/testing may continue but approval remains BLOCKED.

## Evidence
Exact-source hashes, changed-file manifest, deterministic engine views, performance records, applicable save/device matrices, raw critic inputs/outputs, deterministic supplements, known failures and final dispositions are mandatory before APPROVED. Use `specialist_evidence_manifest.py` for static C3/C4/C7/C8/C10/C11 inputs and interim C5 screening. Final C1/C2/C5 and scored C6 evidence follow `EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`; C9 uses the actual `security_exploit_harness.py` attack transport. Approval provenance must satisfy the V3.1 retention policy, and T10+ closeout must retain its exact terminal `factory-observation.json` and pass `factory_closeout_gate.py`.

## Scope
Use the authoritative task-specific frozen scope when present. This generated packet does not expand runtime scope.
