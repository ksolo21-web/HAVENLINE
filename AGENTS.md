# HAVENLINE Agent Instructions

## Required starting point
Read `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md`, `Docs/Production/SEQUENTIAL_REPAIR_PLAN.md`, `Docs/Production/task-gates.json`, `Docs/Production/WORKSTREAM_REGISTRY.json`, `Docs/Production/DEPENDENCY_GRAPH.json`, `Docs/Production/PATH_OWNERSHIP.json`, `Docs/Production/CRITIC_MATRIX.json`, and `Docs/Production/PERFORMANCE_BUDGETS.json` FIRST. Then read `Docs/AI/HavenlineProjectContext.md`, the reference-video lock/source manifest, actual reference pixels, current source and current evidence. The archived pre-V2 plan is historical audit evidence, not the active production mechanism.

## Controlled parallel production
The old pure-serial `ONE TASK BUILDS → NEXT TASK BUILDS` rule is superseded by controlled dependency-graph production:
`DEPENDENCY GRAPH → ISOLATED PARALLEL BUILD → CONTROLLED INTEGRATION → IMPACT-BASED REGRESSION → APPLICABLE SPECIALIST CRITICS → FIX/RETEST → APPROVE → UNLOCK DEPENDENTS`.

Only the integration owner may merge production candidates into `codex/havenline-sequential-task-01` or mark an integrated task APPROVED. Worker branches may build in parallel only when dependencies and path ownership allow. A worker branch can be `INTEGRATION_READY`; isolated success is never production approval.

Task states: `LOCKED`, `PREPARED`, `ASSIGNED`, `BUILDING_ISOLATED`, `BUILT_PENDING_DEPENDENCY`, `INTEGRATION_READY`, `INTEGRATING`, `UNDER_REVIEW`, `FIX_REQUIRED`, `APPROVED`, `BLOCKED`.

Forward-going intermediate PASS requires **every applicable mandatory reviewed dimension strictly >9.0 unrounded**, every applicable G1–G14 gate passed, and no unresolved mandatory defect. Target 10/10. Do not retroactively revoke T01/T02 solely because their original gate wording differed.

No averaging, rounding, missing-area exclusion, unchanged rescoring to obtain a desired result, invented scores, or unresolved mandatory defects. Missing/invalid/truncated/low-confidence/incomplete evidence blocks the relevant gate. Preserve raw failures and unsupported observations; verify critic claims against actual pixels/geometry.

A builder/self-review/persona rerun is not an independent critic. Use applicable C1–C11 from `CRITIC_MATRIX.json`. Independent critics require a genuinely separate permitted $0 reviewer/model runtime with provider/model/run ID, candidate hash, inputs and raw output preserved. If unavailable, continue useful construction/testing but leave G12 BLOCKED.

## Path ownership and change requests
Before editing production files, verify the workstream registry, exact base commit and `PATH_OWNERSHIP.json`. No two active workstreams may own overlapping production paths. Do not modify a protected/foreign-owned path. Create a structured request under `Docs/Production/ChangeRequests/`; the integration owner resolves it.

Shared integration paths such as `main.gd`, `outpost_view.gd`, `outpost_simulation.gd`, `outpost_surface.gd`, the reference contract and coordination registries are integration-owner-only unless explicitly reassigned.

A stale task branch may not silently merge over newer integration work. Reconcile/rebase to the current integration candidate, rerun affected tests, and recapture affected evidence before integration.

## Integration owner procedure
For each candidate: verify assignment; base commit; owned/protected paths; changed files; reconcile stale base; integrate cleanly; run change-impact detection; run mandatory regression; capture fresh integration evidence; run applicable independent critics; fix/retest any mandatory score <=9.0 or gate failure; only then approve, update registry and unlock dependents.

Use `tools/havenline/production/production_cli.py` for registry/path validation, impact selection, regression planning, frozen task packets, capture/motion plans, save/device matrices, evidence packaging and closure validation. These tools are validators/coordinators, not independent critics and not physical-device certification.

## Current protected production state
Repository truth controls. T01 and T02 are approved and remain authoritative unless a later regression reopens them. T03 retains its existing frozen scope and current production checkpoint; do not restart or throw away its work. T04+ runtime work remains locked until T03 passes. Governance/QA tooling may continue without expanding T03 runtime scope.

After T03 approval, Wave 1 may assign T04 camera/composition, T05 station/prop kit and T06 Character 1 motion in isolated non-overlapping branches, plus QA/integration infrastructure. Dependency graph and path ownership, not elapsed time or task number alone, control later parallelism.

## Permanent Havenline gameplay identity
Havenline stays simple and immediate:
`MOVE → AUTO-INTERACT → GATHER → VISIBLY CARRY → DELIVER → TRANSFORM → RESCUE → BUILD/UPGRADE → EXPLORE → DEFEND`.

One primary movement joystick. Auto collect, gather/harvest, attack, contextual unload/deposit and rescue/interactions. Minimal contextual controls only for genuine choices. No button-heavy RPG combat, 4X warfare, complicated manual inventory management, mandatory guilds/guild war, free-text global chat, mandatory multiplayer, unrestricted building or energy systems in Havenline 1.0.

Launch contract remains Level 1–100, connected world, visible progression, spend-blind Challenge Director, seven companion species, weather/day-night, survivor workers, production, defense, physical carrying, world transformation, monetization/VIP, LiveOps, security and phone/tablet/foldable support. Challenge Director may never consume spend/VIP/purchase signals. F2P completion must remain realistic.

## Preserve the actual project
- Active Android project: `HavenlineGodot/`, Godot 4.7.2. Unity is retired.
- Preserve original character/model identities, geometry, skinning, textures, saves and validated fixes.
- C1/C2 selectable leads; unselected lead plus C3/C4 helpers. Unlimited logical carrying and movement/proximity gathering, fighting, rescue, deposit, build and repair remain.
- C2–C4 final rigging/motion reviews remain final character tasks (T59–T61).
- Separate customer pool; distinct survivors; no invisible working actors or primitive stand-ins.
- Companions exactly dog, wolf, fox, owl, male lion, white tiger, brown bear; no domestic cats. Legacy cat saves migrate safely to fox.
- Preserve explicit historical progression/save contracts; record conflicts rather than silently rewriting them.

## Reference videos
Both recordings ending `124839` and `124510` remain authoritative observable visual/gameplay standards. Inspect actual source pixels and motion. Match bright sculpted winter scenery, dense blue-white forest, warm cleared work zones, fences, machinery, physical resource/cash stacks, crowds, helpers, pads and visible transformations. No primitive-looking blockout/default/debug materials may pass final art.

## Evidence and performance
Freeze task scope/evidence before scoring. Record exact source/asset/capture hashes, tests, reviewer results, unresolved defects and next action. Deterministic evidence should include applicable front/rear/left/right/3-quarter/gameplay/detail/overhead/day-night-weather/native-4K states. Motion tasks require full real-time/slow cycles, turns, transitions, feet/toes/knees, hands, gear, tails/wings/mane, ground contact and clipping states.

Track geometry, draw calls, materials, texture memory, shader complexity, CPU/GPU frame time where measurable, physics, animation/NPC load, memory and storage footprint. A visually excellent task may still fail G8.

## Physical release gates remain separate
Landscape must adapt automatically to phones/tablets/foldables. Final required native internal width >=3840 and height >=2160 at render scale 1.0 with sustained >=60 FPS on named representative physical phones/tablets for >=30 minutes where specified. T68/T69 alone certify final physical 4K/60. Software rendering/screenshots/counters do not.

Do not send unfinished APKs or assign testing/benchmarking to Kaleb. Final delivery requires complete functionality, reference fidelity, final independent approval, finished art/motion, save/auth/cloud correctness and physical-device evidence.

## Visible progress
Show a progress bar before substantial tool work and update it at verified milestones. Separate active-task iteration, approved tasks and whole-game completion. No fake time-based progress or background-work promises.
