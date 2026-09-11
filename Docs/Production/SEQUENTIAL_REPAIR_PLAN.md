# Havenline — controlled integration repair plan

**Authoritative execution companion to `HAVENLINE_BUILD_PLAN_V2.md`.** The exact pre-V2 serial plan is preserved at `Docs/Production/Archive/SEQUENTIAL_REPAIR_PLAN.pre-v2.2026-09-11.md` with provenance. This file supersedes its one-task-only production mechanism, not its accepted history or T01–T03 frozen requirements.

## Forward acceptance rule
For T03 and every future intermediate task, PASS requires every applicable mandatory reviewed dimension to score **strictly >9.0 unrounded**, all applicable G1–G14 gates to pass, and no unresolved mandatory defect. Target remains 10/10. T01/T02 are not retroactively revoked merely because their original gate wording differed.

## Production model
`DEPENDENCY GRAPH → ISOLATED PARALLEL BUILD → CONTROLLED INTEGRATION → IMPACT-BASED REGRESSION → APPLICABLE SPECIALIST CRITICS → FIX/RETEST → APPROVE → UNLOCK DEPENDENTS`.

Only the integration owner may merge production candidates to `codex/havenline-sequential-task-01`. Worker branches may become `INTEGRATION_READY`; only the integrated candidate may become `APPROVED` after G14.

States: `LOCKED`, `PREPARED`, `ASSIGNED`, `BUILDING_ISOLATED`, `BUILT_PENDING_DEPENDENCY`, `INTEGRATION_READY`, `INTEGRATING`, `UNDER_REVIEW`, `FIX_REQUIRED`, `APPROVED`, `BLOCKED`.

## Preserved requirements
Both authoritative reference videos remain required actual-pixel/motion standards. Preserve original characters/models/identities/saves/validated fixes. Godot 4.7.2 Android is active; Unity is retired. Landscape automatic phone/tablet/foldable adaptation, unlimited logical carrying and movement/proximity actions remain. Companion species are dog, wolf, fox, owl, lion, tiger and bear; no domestic cats. C2–C4 final rig fixes/reviews remain at the final character stage. No unfinished APK or user benchmarking assignment.

Permanent gameplay language: `MOVE → AUTO-INTERACT → GATHER → VISIBLY CARRY → DELIVER → TRANSFORM → RESCUE → BUILD/UPGRADE → EXPLORE → DEFEND`, using one primary joystick and minimal contextual controls.

## T01 frozen scope — preserved approved
Three finished blue-white sculpted conifer variants; layered/scalloped silhouettes; clean reference-matched materials; dense surrounding woodland; resource-tree routing; ground contact; foreground cutaway; geometry workload. Preserve resource quantities, playable bounds and routing. Excludes terrain/work-floor redesign, camera redesign, fences, buildings, machinery, NPCs and later gameplay.

Required evidence remains actual front/rear/side/three-quarter/detail runtime images, moving-camera sequence, gameplay integration, reference crop provenance, source/asset/capture hashes, depletion/cutaway regression, geometry/material checks, workload/resolution and independent C1/C2 review. **T01 remains APPROVED.**

## T02 frozen scope — preserved approved
Terrain/snow/warm work areas plus the persistent map-spanning river authority. The river remains the exact approved `river_v1_mapspan` system using the accepted T02 source, with terrain/water/collision/save-recovery/future-crossing continuity and approved T01 forest preserved. **T02 remains APPROVED.** Later tasks may not silently alter its authoritative river geometry.

## T03 frozen scope — current active production task
Finished camp fences, six intentional gate openings, and navigable packed work lanes. Visual boundary and collision use the same authoritative panel/gate geometry; routes must remain traversable with no invisible obstacles or trap states. Three river-facing openings preserve T02 future crossing reserves; Task 3 does not implement bridges or Task 4+ behavior. Preserve T01 forest and T02 river.

Current recovered T03 checkpoint:
- candidate/integration source under review: `6947849f581db9cfa53a17ff9202ecde1c0ee80c`;
- 16 suites / 807 checks PASS;
- 61 source-bound renders verified, including 11 native 3840×2160 scale-1 captures;
- 22 critic judgments completed;
- combined gate FAILS specifically on `river-gates`: visual-integrity role minimum 2/10, reference-fidelity role minimum 4/10;
- T03 state is therefore **FIX_REQUIRED**, not approved;
- T04+ runtime remains locked until T03 is repaired and passes the forward >9 rule.

## Universal gates
G1 Dependency; G2 Path ownership; G3 Scope; G4 Build/import; G5 Functional; G6 Regression; G7 Evidence provenance; G8 Performance budget; G9 Persistence where applicable; G10 Security/economy where applicable; G11 Accessibility/adaptive UI where applicable; G12 Critic coverage; G13 every mandatory dimension >9.0 unrounded; G14 integrated candidate regression.

## Coordination authority
- `DEPENDENCY_GRAPH.json` — unlock graph.
- `WORKSTREAM_REGISTRY.json` — assignment/state/source registry.
- `PATH_OWNERSHIP.json` — collision protection and change-request rule.
- `CRITIC_MATRIX.json` — C1–C11 applicability.
- `PERFORMANCE_BUDGETS.json` — early resource budgets.
- `REGRESSION_SUITES.json` — change-impact regression mapping.
- `TASK_PACKET_TEMPLATE.md` — frozen builder handoff.
- `tools/havenline/production/` — validators/generators/packaging/closure tooling.

## Release path
The authoritative task names and dependency-based 70-task release path are in `HAVENLINE_BUILD_PLAN_V2.md` and `DEPENDENCY_GRAPH.json`. Numerical order is the release roadmap; actual assignment/unlock follows dependencies and path ownership.

After T03 approval only, controlled Wave 1 may assign T04 camera/composition, T05 station/prop kit, T06 Character 1 motion, plus QA/integration infrastructure. They must use isolated branches and non-overlapping path ownership. Shared runtime changes require a structured `ChangeRequests/` request and integration-owner resolution.

## Final acceptance
T68/T69 remain the only final sustained physical-device native-4K/60 certification tasks. Software renderer screenshots/counters are regression evidence only, not final hardware certification.
