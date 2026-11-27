# Havenline frozen task packet — T58

Generated: 2026-11-27T12:46:07.174474+00:00

## Identity
- Task ID: T58
- Task name: Phone/tablet/foldable functional acceptance
- Workstream ID: UNASSIGNED
- Owner: UNASSIGNED
- Isolated branch: UNASSIGNED
- Exact base integration commit: UNASSIGNED

## Dependencies
Required APPROVED upstream tasks: T43, T54, T55, T56

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
- **C2 — Technical / Visual Integrity Critic**: `tools/havenline/production/critic_harness.py validate-raw --critic C2`; dimensions: geometry_contact, clipping_seams, intentional_gap_integrity, cross_view_integrity.
  - current evidence contract: `Docs/Production/EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`
  - execution scope: Validates evidence retained by an actual separate agent/model review; this command does not perform or invent the visual review.
- **C4 — Gameplay UX / Readability Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: interactable_clarity, danger_clarity, collection_feedback, resource_destination, world_change_clarity, next_action_clarity.
  - evidence categories: gameplay_state, feedback_state
- **C6 — Performance Critic**: `tools/havenline/production/critic_harness.py ingest-performance-review`; dimensions: frame_time, draw_calls, geometry, texture_memory, shader_cost, physics, animation, population, thermal_risk.
  - current evidence contract: `Docs/Production/EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`
  - execution scope: Current final evidence combines unchanged independent scores and exact hash-bound measurements. The measurement gate alone cannot approve the critic.
- **C11 — Accessibility Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: touch_targets, ui_scale, text_readability, color_differentiation, reduced_motion, subtitles, joystick_layout, controller_state, adaptive_layout.
  - deterministic supplement: `tools/havenline/production/domain_safeguard_gate.py accessibility`
  - device/layout harness: `tools/havenline/production/device_matrix.py`
  - evidence categories: adaptive_ui, accessibility_metrics, device_matrix

## Resource / tool / actor / animation contract
- N/A for this task under the current forward policy. Do not expand frozen scope merely because the contract exists.

## Registered forward contracts
- none registered for this task.

## Forward execution profile — machine resolved
- Standard: `Docs/Production/FORWARD_EXECUTION_STANDARD.md`
- Resolver: `python3 tools/havenline/production/forward_execution.py plan T58`
- Archetype: `platform_ux`
- Execution mode: `validation_only`
- Dependency states: `T43=LOCKED, T54=LOCKED, T55=LOCKED, T56=LOCKED`
- Dependencies currently approved: `false`
- Canonical packet currently present: `false`
- Activation ready now: `false`
- Early sentinel: phone/tablet/foldable layout matrix, rotation/resume, touch/controller paths and save continuity
- Ordered fail-fast gates:
  1. `scope_dependency`
  2. `ownership`
  3. `source_contract`
  4. `focused_unit`
  5. `task_sentinel`
  6. `save_matrix`
  7. `device_matrix`
  8. `impacted_regression`
  9. `performance`
  10. `visual_evidence`
  11. `critic_review`
  12. `closeout`
- Terminal-failure disposition: C0 -> change request to owning build task; this task may not repair runtime
- Exact-SHA rule: finish the candidate already under review; newer candidates queue. Do not use `cancel-in-progress: true` for task candidate review.
- Do not run expensive downstream evidence after an earlier required gate fails. Preserve the exact failure and invoke C0.
- This task is not a runtime-repair owner. A discovered runtime defect must be routed through C0/change request to the owning build task.

## Production Architecture V3 — machine resolved
- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V3.md`
- V3 readiness: `python3 tools/havenline/production/architecture_v3.py readiness T58`
- Feasibility state: `PREP_ONLY`
- Runtime activation allowed now: `false`
- Capability blockers: c0_advisor, independent_critic_runtime
- Scheduler class: `PREP_ONLY`; deterministic priority score: `85` (scheduling heuristic only, never an acceptance score).
- Produces versioned contracts: none
- Consumes versioned contracts: persistence_schema, region_transition, accessibility_layout
- Before runtime activation: resolve all required capabilities; unknown external/hardware prerequisites are not READY.
- Before integration: run `synthetic_merge_forecast.py` against the current integration head and validate any affected shared contract change.
- Gate proof reuse is allowed only through `gate_fingerprint.py`; exact-source-only gates remain fresh and failed results can never be reused as PASS.
- C0 must query `FAILURE_INTELLIGENCE.json` before repair; historical matches are advisory and require confirmation from current evidence.
- **DO NOT start runtime implementation from this packet yet.** Preparation is allowed, but the recorded V3 activation blocker(s) must clear first.

## Production Architecture V3.1 — machine resolved
- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V31_STANDARD.md`
- V3.1 readiness: `python3 tools/havenline/production/architecture_v31.py readiness T58`
- Canonical task-state snapshot: `python3 tools/havenline/production/task_state_snapshot.py T58`
- Every terminal task validation must preserve `factory-observation.json` generated by `tools/havenline/production/factory_observer.py` from the exact GitHub run/jobs/artifacts. C0 does this automatically for terminal failures; success/closeout workflows must do the same before APPROVED.
- Before T10+ approval, run `python3 tools/havenline/production/factory_closeout_gate.py --task T58 --candidate <SHA> --observation <factory-observation.json>`; this gate validates the observation but never grants approval by itself.
- Factory observation produces queue/run/gate telemetry, exact-environment flake observations, the derived task-state snapshot, and any exact-source runtime dependency traces. It is evidence, never a second lifecycle authority.
- Persistent flake history may change diagnosis/retry routing only; a mandatory flaky gate still blocks approval. If runner provenance is missing or ambiguous, flake observations are suppressed rather than guessed.
- Pipeline telemetry records queue/run/gate cost for factory optimization; it cannot change quality thresholds.
- Environment-sensitive proof reuse requires matching runner/toolchain provenance under `CI_TOOLCHAIN_LOCK.json`.
- Approval closeout must satisfy `EVIDENCE_RETENTION_POLICY.json`; artifact expiry cannot erase approval provenance.
- Runtime-observed dependencies are additive only and may add regression suites, never remove static mandatory coverage.
- Mutation canaries must pass before architecture closeout.
- If this task or a consumed contract is reopened, run `python3 tools/havenline/production/proof_invalidation.py task T58` or the affected contract form before reusing downstream proof.
- V3.1 runtime activation allowed now: `false`
- **DO NOT start runtime implementation from this packet yet.** V3 capabilities may be ready, but V3.1 lifecycle, ownership, or canonical-state blockers must clear first.

## Production Architecture V3.2 — machine resolved
- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V32_STANDARD.md`
- V3.2 readiness: `python3 tools/havenline/production/architecture_v32.py readiness T58`
- Parallel-preparation class: `PREP_NOW`; safe work: packet, frozen_scope, reference_lock, fixtures, test_scaffold, schema, asset_audit, capability_check, critic_scaffold, performance_allocation, save_security_cases
- Packet-local ASSIGNED graduation result (remote lineage proof is resolved only at activation): `false`
- Timeout-safe stage shards: `9`; critic fan-out lanes: `4`
- Before ASSIGNED: prove exact control-plane lineage with `python3 tools/havenline/production/task_graduation_gate.py T58 --target ASSIGNED --builder-head <EXACT_BUILDER_HEAD> --integration-head <EXACT_CURRENT_INTEGRATION_HEAD>`.
- Governance-only drift may preserve frozen scope/prepared runtime work, but it never waives control-plane synchronization. `control_plane_lineage.py` must show the integration head is an ancestor of the builder head.
- Claim ASSIGNED only through `python3 tools/havenline/production/v32_assignment_claim.py T58 --owner <OWNER> --branch <BRANCH> --base <EXACT_RECONCILED_INTEGRATION_HEAD> --owned-alias <ALIAS> --builder-head <EXACT_BUILDER_HEAD> --integration-head <EXACT_CURRENT_INTEGRATION_HEAD>`; it verifies the actual remote branch tips and records the assignment binding.
- Before BUILDING_ISOLATED: create `Docs/Production/T58/GRADUATION.json` and pass `python3 tools/havenline/production/task_graduation_gate.py T58 --target BUILDING_ISOLATED`.
- Initialize/update `execution_checkpoint.py`; on timeout preserve `INFRASTRUCTURE_FAILURE` and resume the same exact SHA/stage instead of restarting the task.
- Run `python3 tools/havenline/production/timeout_stage_plan.py T58`; do not combine unrelated expensive stages into one uncheckpointed job.
- Task workflows must call `havenline-v32-task-preflight.yml` as the shared control plane: `mode: preflight` before expensive build work, `mode: review` after source-bound specialist evidence exists, and `mode: failure` under `if: failure()` for task-local failures.
- The shared control plane owns exact builder/candidate/integration lineage binding, graduation, remote branch budget, gate-fingerprint decisions, synthetic-merge/contract checks, checkpoint resume validation, critic-package preflight, specialist fan-out, and C0 routing. C1/C2 and deterministic C6/C9 remain in their required task-specific lanes.
- If three blockers accumulate on one frozen candidate, `blocker_family_gate.py` requires causal-family reconciliation before another candidate.
- Use `critic_invalidation.py` to preserve unchanged same-SHA critic passes; a source-SHA change still requires fresh exact-source review where V3/V3.1 require it.
- Rolling prevention canaries: `python3 tools/havenline/production/rolling_canary.py requirements T58`.
- Record cumulative workload pressure with `performance_ledger.py`; C6 quality scores cannot waive performance budgets or reserved headroom.
- After a deterministic/source-bound gate PASS, stage a content-addressed proof record with `gate_result_recorder.py proposal`; CI cannot promote it. Only the integration owner may apply a verified proposal into `GATE_RESULT_INDEX.json`.
- C0 automatically stages unverified failure-learning proposals. They remain advisory/non-authoritative until a verified post-repair proof plus explicit integration-owner disposition promotes one into `FAILURE_INTELLIGENCE.json`.
- Parallel preparation of later tasks is encouraged only inside GREEN/YELLOW boundaries; it never grants integration or approval.

## Whole-game stakes, useful companions and resource value

Forward requirements: `Docs/Production/GAMEPLAY_DEPTH_STANDARD.md` and `GAMEPLAY_DEPTH_CONTRACT.json`. This addendum does not reopen frozen historical scope, change dependencies/ownership, activate a task, or certify runtime behavior. Use the existing scope/change process for a changed approved component. Owner/consumer labels are responsibilities, not new dependency edges.

- **GD06 — Intelligent stable coordinated work (consumer)**: Implement the fourteen testable AI details in the actor contract: eligibility, stable priorities, shared reservations, safe preemption, player agency, route/target recovery, custody, fairness, survival awareness, truthful perception, save continuity, budgets and readable intent. Evidence: AC03–AC05 interruption/race scenarios; No duplicate claims or depleted-target loops; Simple-control usability; Stuck/abandoned-job evidence and measured busy-shift cost.
- **GD12 — Action-complete audio and accessible feedback (consumer)**: Feature owners emit truthful event phases; T54 freezes cue/mix/music/ambience or justified silence and listening evidence for each applicable event, variant and interruption. Critical information remains readable muted/reduced motion. Evidence: Per-event sound/music disposition; Actual listening under busy mixed activity; No success sound on denied/replayed transaction; Priority/concurrency/accessibility evidence.
- **GD17 — Integrated busy-shift and device proof (owner)**: Measure concurrent working humans, pets, enemies, machines and deliveries with interruption/recovery on target devices. Visual/decision scaling preserves gameplay truth and readable attacks; planning checks cannot establish FPS or population capacity. Evidence: AC10 device/population scenario; Sustained source-bound CPU/GPU/memory and frame evidence; Busy-cycle and muted/reduced-motion review; No full-cost path recomputation for every idle actor.

Task-specific actor/motion details:

- Actual phone/tablet/foldable interaction, suspension and viewport coverage.

Use the complete source-bound resource ledger and actor scenarios under `Docs/Production/GameplayDepth/2026-11-27/`. The introducing task freezes a useful resource contract before its own integration; T33 later reconciles it. Each pet proves standalone usefulness before T31 integration. All future play scenarios remain untested by this planning audit. Preserve the existing >=9.9 and stronger exact-10 reference rules.

## Current whole-game decisions and gap closure

Read `Docs/Production/COMPLETENESS_STANDARD.md`, `WHOLE_GAME_COMPLETENESS.json` and `CURRENT_GAMEPLAY_SOURCE.json`. The CD choices supersede the earlier D01–D05 open behavior wording; numeric tuning and actual game evidence remain open. These responsibilities are not new dependency edges or task activation, and preserve frozen historical scope.

- **CG05 — Useful active team and reserve population (consumer):** Three field pets and two survivor escorts, with useful camp assignments and conserved offscreen active-session work. Ownership, deployment and injury are separate states. Required evidence: Swap at safe camp with cargo/injury/recovery preserved.; No cooldown reset, cloned actor or invented unseen combat rewards.; Actual population census and sustained busy-scene proof.
- **CG11 — Learnability and simple controls across systems (consumer):** Teach one useful loop at first use; show next goal, material purpose, threat consequence, helper intent and denial reason in context. Retain one primary movement control and concise deliberate choices. Required evidence: Fresh, returning and resumed player comprehension.; Busy camp selection, cancel, auto-interaction and accessible critical cues without required dashboard use.
- **CG15 — Reference and render fidelity at every use state (consumer):** Use pinned selected GitHub references with explicit observed/authored/inferred distinctions. Current candidate must meet>=9.9 reference dimensions and every stronger exact10 visual rule; historical static scores do not pass runtime. Required evidence: Exact image/model/rig/scene/clip/source identity.; Actual matched-camera play and full motion evidence; no average hides a failed area.; Missing source or tiny unidentified figure stays unresolved rather than guessed.
- **CG16 — One unambiguous gameplay continuation source (consumer):** Use CURRENT_GAMEPLAY_SOURCE.json and corrected root entrypoints: newer Codex field project; main/alfred commands are explicitly historical. Resolve actual live head and owner before edits. Required evidence: Entry-point guidance agrees on branch/project/scene.; No runtime merge, branch reassignment or historical receipt rewrite.
- **CG17 — Landscape, real aspect-ratio coverage and device truth (owner):** Correct phone16:9 dimensions and validate profile identity/aspect before running adapters; bind landscape configuration to shipping source. Required evidence: Distinct16:9/20:9 states, tablet native rounding tolerated, fold/resume/save/input cases.; Unsupported portrait cannot leak into release.; Layout test success never certifies physical native4K60.
- **CG18 — Accessibility across actual play states (consumer):** Apply existing readable text/contrast/non-color cues/touch size/reduced motion/subtitles/input preferences to threats, helper intent, resource purpose, care, payments and event expiry. Persist preferences. Required evidence: First-use/busy-camp/denied/resume states readable muted and reduced-motion.; Quality/orientation/fold changes preserve hit targets and input release; no hidden critical cue.
- **CG23 — Evidence-bound integrated release (consumer):** Keep final candidates immutable and exact-source-bound; integrate full-route, free progression, commerce, events, exploit, regression and physical device evidence. Route repairs to owners and reopen affected approvals. Required evidence: Fresh install/update/reinstall/migration/recovery for the actual signed candidate.; All mandatory evidence and independent scores pass; planning checks cannot certify play.

Applicable selected decisions: CD04, CD05, CD10.
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
