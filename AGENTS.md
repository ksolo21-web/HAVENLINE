# HAVENLINE Agent Instructions — V2 Controlled Parallel Production

## Required starting point

Read in this order before any Havenline production work:

1. `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md`
2. `Docs/Production/SEQUENTIAL_REPAIR_PLAN.md`
3. `Docs/Production/task-gates.json`
4. `Docs/Production/WORKSTREAM_REGISTRY.json`
5. `Docs/Production/DEPENDENCY_GRAPH.json`
6. `Docs/Production/PATH_OWNERSHIP.json`
7. `Docs/Production/CRITIC_MATRIX.json`
8. `Docs/Production/PERFORMANCE_BUDGETS.json`
9. the active task packet/frozen scope
10. `Docs/AI/HavenlineProjectContext.md`
11. `Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md`, its source manifest, and actual reference pixels.

Inspect current source/evidence for newer work. `Docs/AI/UnityProjectContext.md` is historical.

## Current migration checkpoint

T01 and T02 are APPROVED at their recorded accepted sources. Do not restart or
retroactively revoke them merely because the forward gate is stricter.

T03 is ACTIVE / FIX_REQUIRED at `Docs/Production/T03/FROZEN_SCOPE.md`. Its
latest reviewed exact candidate before V2 migration is
`6947849f581db9cfa53a17ff9202ecde1c0ee80c`; 16 suites / 807 checks passed,
but the latest combined C1/C2 gate still rejected the `river-gates` group.
T04+ runtime production remains LOCKED until T03 is APPROVED.

T03 is the only legacy task grandfathered to finish directly on
`codex/havenline-sequential-task-01` because its runtime work was already
integrated before this governance migration. All future runtime work uses
isolated task branches.

## Forward acceptance rule

For every not-yet-approved task, PASS requires every applicable mandatory
review dimension to score **strictly greater than 9.0, unrounded**, all
applicable gates G1-G14 to pass, complete required critic coverage, and zero
unresolved mandatory defects. Target is 10/10.

No averaging, rounding, missing-area exclusion, unchanged rescoring to obtain a
desired number, invented scores, or unresolved mandatory defects. Missing,
invalid, truncated, low-confidence or incomplete required evidence blocks
approval.

## Controlled parallel-production rule

Production flow is:

DEPENDENCY GRAPH -> TASK PACKET -> CLAIM DISJOINT PATHS -> BUILD ISOLATED ->
TEST -> PACKAGE CANDIDATE -> INTEGRATION OWNER REVIEW -> RECONCILE STALE BASE ->
INTEGRATE -> IMPACT REGRESSION -> FRESH INTEGRATION EVIDENCE -> APPLICABLE
CRITICS -> FIX/RETEST -> APPROVE -> UNLOCK DEPENDENTS.

Only the integration owner may integrate production candidates onto the
integration branch. A builder may reach `INTEGRATION_READY` but may never
self-declare production approval.

No two active workstreams may own the same production file/path. If a builder
needs a path owned by another workstream or marked integration-only, DO NOT
MODIFY IT. Create a structured request under
`Docs/Production/ChangeRequests/`. The integration owner resolves it.

Before integration, a stale task must reconcile against the current integration
candidate, rerun affected tests and recapture affected evidence.

## Task states

LOCKED, PREPARED, ASSIGNED, BUILDING_ISOLATED, BUILT_PENDING_DEPENDENCY,
INTEGRATION_READY, INTEGRATING, UNDER_REVIEW, FIX_REQUIRED, APPROVED, BLOCKED.

Status never advances because time passed.

## Havenline gameplay identity

Permanent gameplay language:

MOVE -> AUTO-INTERACT -> GATHER -> VISIBLY CARRY -> DELIVER -> TRANSFORM ->
RESCUE -> BUILD/UPGRADE -> EXPLORE -> DEFEND.

Permanent control philosophy:

- one primary movement joystick;
- auto collect;
- auto gather/harvest;
- auto attack;
- automatic contextual unloading/deposit;
- automatic contextual rescue/interactions;
- minimal contextual controls only when a deliberate choice genuinely requires them.

Do not evolve Havenline into button-heavy RPG combat, 4X warfare, complicated
manual inventory, mandatory multiplayer, unrestricted building, guild warfare,
free-text global chat, or an energy-wall game. Depth, scale and difficulty may
grow; control complexity should not.

## Preserve the actual project

- Active Android project: `HavenlineGodot/`, Godot 4.7.2. Unity is retired.
  No Unity install/license/runtime/build/IL2CPP path.
- Preserve original character/model identities, geometry, skinning, textures,
  saves and validated fixes. Never silently revert to older checkpoints.
- C1/C2 are selectable leads; unselected lead is helper with C3/C4.
- Unlimited logical carrying and movement/proximity gathering, fighting,
  rescue, deposit, build and repair remain required. No manual-action-button
  substitute.
- C2-C4 final rigging/final rig reviews remain T59-T61.
- Customers remain separate reusable two-male/two-female bases with persistent
  identities. Survivors and animal companions do not replace them.
- Missing authored NPCs cannot become invisible working actors or primitive
  stand-ins. Keep readiness explicit in `data/npc-catalog.json`.
- Animal companions are exactly guardian dog, gray wolf, fox, owl, male lion,
  white tiger and brown bear. No domestic cats. Legacy cat saves migrate to fox
  without losing identity/recruitment/assignment/rescue progress.
- Preserve historical progression/save contracts; record conflicts instead of
  silently rewriting distinct actions or prices.

## Both reference videos are authoritative

The recordings ending `124839` and `124510` are the observable visual/gameplay
standard, not loose inspiration. Inspect actual source pixels and motion.

Both loops remain required: fishing/food/customer service/reinvestment AND
harvesting/hunting/camp supply/weapon upgrades/defenses. Match bright sculpted
winter scenery, dense blue-white forest, warm cleared work zones, fences,
machinery, tall moving resource/cash stacks, crowds, helpers, pads and visible
paid transformations. Generic cabin/furnace clearing is not the target.
Photorealism/noise/polygon count is not automatically closer. No primitive
blockout/default/debug material may pass as finished art.

## Monetization and LiveOps

No energy wall, mandatory payment, fake discounts, hidden spend-based
difficulty, or intentionally miserable F2P. Challenge Director may never
consume purchase history/VIP/spend signals. One primary premium currency.
VIP is permanent and transparent. Level 1-100 must remain realistically
completable at $0.

Launch LiveOps retains The First Thaw, weekly gameplay event, weekly sale
rotation, seasonal/holiday frameworks, server-authoritative time, automatic
validated scheduling, pre-approved event composition and remote kill switch.

## Evidence and critics

Use the task packet and `CRITIC_MATRIX.json`. Builder self-review, a second
persona, or a second prompt from the builder is NOT an independent critic.
Use a genuinely separate reviewer/model runtime when required and permitted at
$0. Record provider/model, run/session/request ID, candidate hash, exact inputs
and raw output. If no independent runtime is available, continue useful work
but leave that gate BLOCKED. Do not introduce paid critic APIs.

C6 quantitative performance review and C9 adversarial security harnesses may be
deterministic specialist gates; they still require preserved raw measurement
or attack evidence and cannot be hand-waved.

## Regression and path ownership

Run `tools/havenline/production/change_impact.py` on candidate changes, then
`regression_runner.py` for the union of universal and impacted mandatory
suites. Unknown production changes fall back to the full current mandatory
suite set.

Run `workstream.py validate-candidate` before integration. Unauthorized
foreign/protected path modifications fail G2. A needed shared-path edit becomes
a change request rather than an opportunistic builder edit.

## Persistence, device and evidence matrices

Use `SAVE_STATE_MATRIX.json` for fresh/current/previous/interrupted/reload/
migration/rollback cases where applicable.

Use `DEVICE_LAYOUT_MATRIX.json` early for phone/tablet/foldable functional
states. Shipping remains landscape and automatically adaptive; no manual device
selector.

Use deterministic evidence capture metadata: candidate commit/hash, scene/state,
camera, renderer, resolution, build/run ID and timestamp. Visual tasks capture
front/rear/left/right/3/4/gameplay/detail/overhead/conditions/native-4K where
applicable. Motion tasks capture full real-time/slow cycles, turns, transitions,
feet/toes/knees/hands, gear, tails/wings/mane and contact/clipping states.

## Performance and release

`PERFORMANCE_BUDGETS.json` protects full-game headroom. A visually excellent
task may still fail G8 when it consumes an unsustainable share of CPU/GPU/
memory/geometry/physics/animation/resource budget.

Final physical release still requires native internal width >=3840 and height
>=2160, scale 1.0, sustained >=60 FPS on representative named physical phones
AND tablets/foldables under completed-game load for at least 30 minutes, with
presentation timing, resolution and thermal evidence. Only T68/T69 certify
that. Software rendering, screenshots or engine counters do not.

Kaleb must not receive unfinished APKs or be asked to test/benchmark them.
Internal isolated-package builds may continue.

## Visible progress

Before substantial work, show an explicit commentary progress bar. Update it at
verified milestones with current stage, completed/total count, latest verified
result and next blocker/action. Do not fabricate time-based percentages or
promise unscheduled background work.

## Failure handling

Work through genuine failures: diagnose, preserve working checkpoints, change
approach when justified, fix and rerun. Do not lower thresholds to finish.
Record exact source/asset/capture hashes, tests, raw critic results, unresolved
defects and the next executable action after each cycle.
