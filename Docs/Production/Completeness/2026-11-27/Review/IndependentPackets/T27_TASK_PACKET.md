# Havenline frozen task packet — T27

Generated: 2026-11-27T12:46:06.572546+00:00

## Identity
- Task ID: T27
- Task name: Owl
- Workstream ID: UNASSIGNED
- Owner: UNASSIGNED
- Isolated branch: UNASSIGNED
- Exact base integration commit: UNASSIGNED

## Dependencies
Required APPROVED upstream tasks: T06, T07, T14

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
- **C5 — Motion / Rigging Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: full_cycle, foot_contact, lower_body_mechanics, upper_body_mechanics, weight_transfer, transitions, clipping, secondary_motion_contact.
  - required capture harness: `tools/havenline/production/motion_capture.py`
  - current evidence contract: `Docs/Production/EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`
  - evidence categories: motion_cycle, motion_transition, contact_detail
  - final approval unavailable through this runner: A separate source-bound independent review must actually inspect the full motion cycles and transitions through playback. This contact-sheet runner cannot grant final C5 approval.
- **C6 — Performance Critic**: `tools/havenline/production/critic_harness.py ingest-performance-review`; dimensions: frame_time, draw_calls, geometry, texture_memory, shader_cost, physics, animation, population, thermal_risk.
  - current evidence contract: `Docs/Production/EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`
  - execution scope: Current final evidence combines unchanged independent scores and exact hash-bound measurements. The measurement gate alone cannot approve the critic.

## Resource / tool / actor / animation contract
- REQUIRED by `Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md`.
- Resource registry SHA256: `8e9feba3a92972b10ac7dc8589e43bd0f988c2981ffe0fcace2edb1100e3bd9d`
- Actor capability matrix SHA256: `f319469be543267c6a21988d6b23f915550bd01c7d8513516b7410915680b1bf`
- Animation action matrix SHA256: `57df079f213a88e58b87e01aa7b520ca2fe4d98a41368307fdbba433a57d46e5`
- Resources this task must resolve/prove: none predeclared; any introduced resource must still be registered
- Actor capability keys this task must prove: owl
- Animation profiles this task must prove: owl_attack, owl_retrieve, owl_flight, owl_takeoff, owl_landing
- Run `python3 tools/havenline/production/resource_actor_contract.py --task T27 --manifest <candidate-manifest> --output <proof.json>` before closure.

## Registered forward contracts
- none registered for this task.

## Forward execution profile — machine resolved
- Standard: `Docs/Production/FORWARD_EXECUTION_STANDARD.md`
- Resolver: `python3 tools/havenline/production/forward_execution.py plan T27`
- Archetype: `action_motion`
- Execution mode: `build`
- Dependency states: `T06=APPROVED, T07=APPROVED, T14=LOCKED`
- Dependencies currently approved: `false`
- Canonical packet currently present: `false`
- Activation ready now: `false`
- Early sentinel: owl flight, takeoff/landing, wing clearance, aerial navigation, retrieve/scout and dive/talon contact
- Ordered fail-fast gates:
  1. `scope_dependency`
  2. `ownership`
  3. `reference_lock`
  4. `source_contract`
  5. `focused_unit`
  6. `task_sentinel`
  7. `motion_preflight`
  8. `save_matrix`
  9. `impacted_regression`
  10. `performance`
  11. `visual_evidence`
  12. `critic_review`
  13. `integration`
  14. `post_integration_regression`
  15. `closeout`
- Terminal-failure disposition: C0 -> bounded builder repair plan
- Exact-SHA rule: finish the candidate already under review; newer candidates queue. Do not use `cancel-in-progress: true` for task candidate review.
- Do not run expensive downstream evidence after an earlier required gate fails. Preserve the exact failure and invoke C0.

## Production Architecture V3 — machine resolved
- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V3.md`
- V3 readiness: `python3 tools/havenline/production/architecture_v3.py readiness T27`
- Feasibility state: `PREP_ONLY`
- Runtime activation allowed now: `false`
- Capability blockers: android_build_toolchain, c0_advisor, independent_critic_runtime
- Scheduler class: `PREP_ONLY`; deterministic priority score: `167` (scheduling heuristic only, never an acceptance score).
- Produces versioned contracts: none
- Consumes versioned contracts: context_action_identity, persistence_schema, population_actor
- Before runtime activation: resolve all required capabilities; unknown external/hardware prerequisites are not READY.
- Before integration: run `synthetic_merge_forecast.py` against the current integration head and validate any affected shared contract change.
- Gate proof reuse is allowed only through `gate_fingerprint.py`; exact-source-only gates remain fresh and failed results can never be reused as PASS.
- C0 must query `FAILURE_INTELLIGENCE.json` before repair; historical matches are advisory and require confirmation from current evidence.
- **DO NOT start runtime implementation from this packet yet.** Preparation is allowed, but the recorded V3 activation blocker(s) must clear first.

## Production Architecture V3.1 — machine resolved
- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V31_STANDARD.md`
- V3.1 readiness: `python3 tools/havenline/production/architecture_v31.py readiness T27`
- Canonical task-state snapshot: `python3 tools/havenline/production/task_state_snapshot.py T27`
- Every terminal task validation must preserve `factory-observation.json` generated by `tools/havenline/production/factory_observer.py` from the exact GitHub run/jobs/artifacts. C0 does this automatically for terminal failures; success/closeout workflows must do the same before APPROVED.
- Before T10+ approval, run `python3 tools/havenline/production/factory_closeout_gate.py --task T27 --candidate <SHA> --observation <factory-observation.json>`; this gate validates the observation but never grants approval by itself.
- Factory observation produces queue/run/gate telemetry, exact-environment flake observations, the derived task-state snapshot, and any exact-source runtime dependency traces. It is evidence, never a second lifecycle authority.
- Persistent flake history may change diagnosis/retry routing only; a mandatory flaky gate still blocks approval. If runner provenance is missing or ambiguous, flake observations are suppressed rather than guessed.
- Pipeline telemetry records queue/run/gate cost for factory optimization; it cannot change quality thresholds.
- Environment-sensitive proof reuse requires matching runner/toolchain provenance under `CI_TOOLCHAIN_LOCK.json`.
- Approval closeout must satisfy `EVIDENCE_RETENTION_POLICY.json`; artifact expiry cannot erase approval provenance.
- Runtime-observed dependencies are additive only and may add regression suites, never remove static mandatory coverage.
- Mutation canaries must pass before architecture closeout.
- If this task or a consumed contract is reopened, run `python3 tools/havenline/production/proof_invalidation.py task T27` or the affected contract form before reusing downstream proof.
- V3.1 runtime activation allowed now: `false`
- **DO NOT start runtime implementation from this packet yet.** V3 capabilities may be ready, but V3.1 lifecycle, ownership, or canonical-state blockers must clear first.

## Production Architecture V3.2 — machine resolved
- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V32_STANDARD.md`
- V3.2 readiness: `python3 tools/havenline/production/architecture_v32.py readiness T27`
- Parallel-preparation class: `PREP_NOW`; safe work: packet, frozen_scope, reference_lock, fixtures, test_scaffold, schema, asset_audit, capability_check, critic_scaffold, performance_allocation, save_security_cases
- Packet-local ASSIGNED graduation result (remote lineage proof is resolved only at activation): `false`
- Timeout-safe stage shards: `10`; critic fan-out lanes: `4`
- Before ASSIGNED: prove exact control-plane lineage with `python3 tools/havenline/production/task_graduation_gate.py T27 --target ASSIGNED --builder-head <EXACT_BUILDER_HEAD> --integration-head <EXACT_CURRENT_INTEGRATION_HEAD>`.
- Governance-only drift may preserve frozen scope/prepared runtime work, but it never waives control-plane synchronization. `control_plane_lineage.py` must show the integration head is an ancestor of the builder head.
- Claim ASSIGNED only through `python3 tools/havenline/production/v32_assignment_claim.py T27 --owner <OWNER> --branch <BRANCH> --base <EXACT_RECONCILED_INTEGRATION_HEAD> --owned-alias <ALIAS> --builder-head <EXACT_BUILDER_HEAD> --integration-head <EXACT_CURRENT_INTEGRATION_HEAD>`; it verifies the actual remote branch tips and records the assignment binding.
- Before BUILDING_ISOLATED: create `Docs/Production/T27/GRADUATION.json` and pass `python3 tools/havenline/production/task_graduation_gate.py T27 --target BUILDING_ISOLATED`.
- Initialize/update `execution_checkpoint.py`; on timeout preserve `INFRASTRUCTURE_FAILURE` and resume the same exact SHA/stage instead of restarting the task.
- Run `python3 tools/havenline/production/timeout_stage_plan.py T27`; do not combine unrelated expensive stages into one uncheckpointed job.
- Task workflows must call `havenline-v32-task-preflight.yml` as the shared control plane: `mode: preflight` before expensive build work, `mode: review` after source-bound specialist evidence exists, and `mode: failure` under `if: failure()` for task-local failures.
- The shared control plane owns exact builder/candidate/integration lineage binding, graduation, remote branch budget, gate-fingerprint decisions, synthetic-merge/contract checks, checkpoint resume validation, critic-package preflight, specialist fan-out, and C0 routing. C1/C2 and deterministic C6/C9 remain in their required task-specific lanes.
- If three blockers accumulate on one frozen candidate, `blocker_family_gate.py` requires causal-family reconciliation before another candidate.
- Use `critic_invalidation.py` to preserve unchanged same-SHA critic passes; a source-SHA change still requires fresh exact-source review where V3/V3.1 require it.
- Rolling prevention canaries: `python3 tools/havenline/production/rolling_canary.py requirements T27`.
- Record cumulative workload pressure with `performance_ledger.py`; C6 quality scores cannot waive performance budgets or reserved headroom.
- After a deterministic/source-bound gate PASS, stage a content-addressed proof record with `gate_result_recorder.py proposal`; CI cannot promote it. Only the integration owner may apply a verified proposal into `GATE_RESULT_INDEX.json`.
- C0 automatically stages unverified failure-learning proposals. They remain advisory/non-authoritative until a verified post-repair proof plus explicit integration-owner disposition promotes one into `FAILURE_INTELLIGENCE.json`.
- Parallel preparation of later tasks is encouraged only inside GREEN/YELLOW boundaries; it never grants integration or approval.

## Whole-game stakes, useful companions and resource value

Forward requirements: `Docs/Production/GAMEPLAY_DEPTH_STANDARD.md` and `GAMEPLAY_DEPTH_CONTRACT.json`. This addendum does not reopen frozen historical scope, change dependencies/ownership, activate a task, or certify runtime behavior. Use the existing scope/change process for a changed approved component. Owner/consumer labels are responsibilities, not new dependency edges.

- **GD07 — Distinct useful seven-companion roster (owner)**: Preserve seven species and existing authored capabilities; prove a distinct useful normal-play role per pet with meaningful player benefit and complete species motion. Recommended role emphases remain explicit authoring choices. Evidence: Individual species-usefulness scenario; Controlled comparison with idle companion; Mixed human/pet team scenario; Distinct-view full work/attack cycles.
- **GD08 — Friendly identity and legitimate target/loot eligibility (owner)**: Separate friendly pets/survivors, wild prey and hostile entities by identity/faction/eligibility. Companion species art never implies friendly actors are harvestable or that each rendered meat cut must enter the food economy. Evidence: Friendly-target and drop exclusion tests; Species/resource eligibility decision; No friendly loot/duplicate rescue farming; Owner-scoped new wildlife decisions.
- **GD09 — Full state/action/transition animation (consumer)**: Cover the twelve animation families, complete loops, transitions, contact, interruption, blocked/full/empty and resume states. Use justified static/shared dispositions where appropriate; no generic placeholder masquerades as finished action. Evidence: Action/state inventory linked to actual clips/mechanisms; Real-time and slow playback from distinct meaningful views; Feet/toes/knees/hands/paws/tails/wings/tool/cargo contact; State-to-authoritative-event alignment.
- **GD11 — Readable enemy and combat variety (consumer)**: Each introduced enemy/weapon/locomotion archetype has authored intent, tell, attack, hit/miss, recovery and response states, with visible range/timing matching damage and meaningful counterplay. Evidence: Per-archetype motion/state evidence; Hit/miss/contact/geometry regression; Combined threat counterplay; No difficulty-only health or invisible damage substitution.
- **GD12 — Action-complete audio and accessible feedback (consumer)**: Feature owners emit truthful event phases; T54 freezes cue/mix/music/ambience or justified silence and listening evidence for each applicable event, variant and interruption. Critical information remains readable muted/reduced motion. Evidence: Per-event sound/music disposition; Actual listening under busy mixed activity; No success sound on denied/replayed transaction; Priority/concurrency/accessibility evidence.

Task-specific actor/motion details:

- owl: preserve existing capabilities; make its distinct role useful in an actual scenario; complete species motion and AI recovery evidence.

Unfrozen design decisions for this owner:

- D04 — Pet role kits and active population: RECOMMENDED_PENDING_OWNER_FREEZE_AND_PLAYTEST. Freeze Per-species role parameters; Team/worker limits; Suitable environments and cargo; Offscreen rules if used.

Use the complete source-bound resource ledger and actor scenarios under `Docs/Production/GameplayDepth/2026-11-27/`. The introducing task freezes a useful resource contract before its own integration; T33 later reconciles it. Each pet proves standalone usefulness before T31 integration. All future play scenarios remain untested by this planning audit. Preserve the existing >=9.9 and stronger exact-10 reference rules.

## Current whole-game decisions and gap closure

Read `Docs/Production/COMPLETENESS_STANDARD.md`, `WHOLE_GAME_COMPLETENESS.json` and `CURRENT_GAMEPLAY_SOURCE.json`. The CD choices supersede the earlier D01–D05 open behavior wording; numeric tuning and actual game evidence remain open. These responsibilities are not new dependency edges or task activation, and preserve frozen historical scope.

- **CG01 — Every pet attacks and contributes a specialty (owner):** Adopt all12 PA rules and seven species/profile/render rows. Support-only fox or owl fails. Required evidence: Seven real positive-damage attack demonstrations.; Each species also completes its useful job; miss/interrupt/recall/return and later suitable-region use are proven.
- **CG03 — Stakes, sanctuary and recoverable actors (consumer):** Protect earned inventory/progress; expose field actors and forward operations to warned, recoverable interruption. Care/recovery is always free and attainable. Required evidence: Zone-by-actor attackability, boundary and repeat-failure tests.; All down/retreat/cargo/payment states recover without duplication or permanent loss.
- **CG04 — Combat roster, useful counters and equipment (consumer):** Use selected bounded hostile/hunt/weapon roster and existing GitHub art. New variants require declared source and proof; extra HP alone is not a distinct enemy behavior. Required evidence: Real telegraph/contact/miss/recovery/counterplay per selected enemy and weapon.; Friendly pets and rescue candidates never become hunt drops.; No protected-actor attack exploit or reset loot at sanctuary; exposed perimeter defenses follow their declared valid domain.
- **CG05 — Useful active team and reserve population (owner):** Three field pets and two survivor escorts, with useful camp assignments and conserved offscreen active-session work. Ownership, deployment and injury are separate states. Required evidence: Swap at safe camp with cargo/injury/recovery preserved.; No cooldown reset, cloned actor or invented unseen combat rewards.; Actual population census and sustained busy-scene proof.
- **CG07 — Ten regions and credible animal access (consumer):** Bind each region to a concrete production/traversal payoff and supported actor routes; unsuitable pet environments use useful safe assignments. Required evidence: Ten-band goals and actor travel/work/attack applicability.; Free return, no stranded cargo, no underwater owl or flying quadruped.
- **CG13 — Smart actors under congestion and change (consumer):** Reserve jobs and approach lanes; bound retries, detect unreachable/depleted/full targets, keep priorities stable and explain a useful fallback. Navigation/avoidance alone does not satisfy smart behavior. Required evidence: Two workers competing for final resources/payment.; Narrow gate, moving target, broken route, full store, changed goal and path recovery.; No actor stuck idle when valid authorized work exists, no target thrashing or unbounded per-frame path replanning.
- **CG14 — Complete action, machine and sound states (owner):** Prove complete start/work/contact/success/miss/blocked/empty/full/cancel/recovery transitions for every applicable actor, machine, tool and transport. Use actual clip/contact/audio bindings. Required evidence: Full cycles and transitions from meaningful angles, feet/toes/knees, attachments and clipping.; Actual sound listening in busy play; mute/reduced-motion equivalents.; No success sound or transfer effect for denied/replayed transaction.
- **CG15 — Reference and render fidelity at every use state (consumer):** Use pinned selected GitHub references with explicit observed/authored/inferred distinctions. Current candidate must meet>=9.9 reference dimensions and every stronger exact10 visual rule; historical static scores do not pass runtime. Required evidence: Exact image/model/rig/scene/clip/source identity.; Actual matched-camera play and full motion evidence; no average hides a failed area.; Missing source or tiny unidentified figure stays unresolved rather than guessed.
- **CG16 — One unambiguous gameplay continuation source (consumer):** Use CURRENT_GAMEPLAY_SOURCE.json and corrected root entrypoints: newer Codex field project; main/alfred commands are explicitly historical. Resolve actual live head and owner before edits. Required evidence: Entry-point guidance agrees on branch/project/scene.; No runtime merge, branch reassignment or historical receipt rewrite.

Applicable selected decisions: CD01, CD02, CD04, CD05, CD06, CD07.
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
