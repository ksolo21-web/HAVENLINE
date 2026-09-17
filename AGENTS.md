# HAVENLINE Agent Instructions — V3 Controlled Parallel Production

## Status/continuity fast path — apply before the full production bootstrap

For a read-only question such as "update on T06", "where did we leave off?",
"what failed?", "what is blocked?", or "what is the next action?", first read
`Docs/Production/AGENT_EXECUTION_LOOP_GUARD.md` and use its authoritative
status fast path.

A simple status/continuity request MUST NOT automatically trigger the full
production reading order below. When the repository/task are already known,
do not rediscover the repository, enumerate unrelated branches, repeatedly
search commits, or widen retrieval merely because more history exists. Stop
retrieving as soon as the current state, last verified milestone, blocker and
next action are supportable.

The full production bootstrap becomes mandatory when the user asks to build,
modify, integrate, review, repair or otherwise change production work.

## Required starting point for production work

Read in this order before any Havenline production work:

1. `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md`
2. `Docs/Production/AGENT_EXECUTION_LOOP_GUARD.md`
3. `Docs/Production/ANTI_LOOP_ROOT_CAUSE_STANDARD.md`
4. `Docs/Production/SEQUENTIAL_REPAIR_PLAN.md`
5. `Docs/Production/FORWARD_EXECUTION_STANDARD.md`
6. `Docs/Production/FORWARD_EXECUTION_PROFILES.json`
7. `Docs/Production/FORWARD_GATE_RUNNERS.json`
8. `Docs/Production/PRODUCTION_ARCHITECTURE_V3.md`
9. `Docs/Production/TASK_CAPABILITY_MATRIX.json`
10. `Docs/Production/CAPABILITY_STATUS.json`
11. `Docs/Production/PRODUCTION_SCHEDULER_POLICY.json`
12. `Docs/Production/GATE_FINGERPRINT_POLICY.json`
13. `Docs/Production/CONTRACT_REGISTRY.json`
14. `Docs/Production/FAILURE_INTELLIGENCE.json`
15. `Docs/Production/task-gates.json`
16. `Docs/Production/GAME_MASTER_ACCOUNT_STANDARD.md`
17. `Docs/Production/GAME_MASTER_POLICY.json`
18. `Docs/Production/WORKSTREAM_REGISTRY.json`
19. `Docs/Production/DEPENDENCY_GRAPH.json`
20. `Docs/Production/PATH_OWNERSHIP.json`
21. `Docs/Production/CRITIC_MATRIX.json`
22. `Docs/Production/PERFORMANCE_BUDGETS.json`
23. the active task packet/frozen scope
24. `Docs/AI/HavenlineProjectContext.md`
25. `Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md`, its source manifest, and actual reference pixels.

Inspect current source/evidence for newer work. `Docs/AI/UnityProjectContext.md` is historical.

## Current production checkpoint

T01, T02 and T03 are APPROVED at their recorded accepted sources. Do not
restart or retroactively revoke them merely because the forward gate is
stricter. T03 is accepted at
`5df9726e0b1c33f0f8865385b1c49aca229fd461`; its verified record is
`Docs/Production/T03/verified-completion.json`.

T04 is APPROVED at accepted gameplay source
`e08fd37e9a999d878644c03089c4b4b253bd7472`; its verified record is
`Docs/Production/T04/verified-completion.json`.

T05 is APPROVED at accepted gameplay source
`fa6fa70f154f3757d22303522ca3f6de2c3d391f`; its verified record is
`Docs/Production/T05/verified-completion.json`.

T06 is APPROVED at accepted isolated source
`47f86fae25b099abb5c7096c37ca7495453b2b8f`, integrated and freshly regressed
at `91f35f331aaabe2b1785b10c0d911f20da6f12d9`; its verified record is
`Docs/Production/T06/verified-completion.json`.

T07 is APPROVED at accepted isolated source
`0a30dc0859541626eb6aa9a9bb749abc93dcb355`, integrated at
`94b3f6c5097356a3857ebd13a77fb1e316eb06ae`; its verified record is
`Docs/Production/T07/verified-completion.json`.

T08 is APPROVED at exact integrated source
`9d56ea8ae972d0a0705ff8b985e13fab31dde493`; its verified closure is recorded
in `Docs/Production/T08/verified-completion.json` after 23 suites / 1535
checks, all 44 locked frames, both locked recordings, G1-G14 and strict
C2/C3/C4/C6 review.

T09 is the active INTEGRATION_READY workstream at
`Docs/Production/T09/FROZEN_SCOPE.md` and `Docs/Production/T09/TASK_PACKET.md`.
Its owner is `harvesting-acquisition-builder`, its isolated branch is
`havenline/T09-harvesting`, and its exact integration base is
`7492074e40a0b061f31d8c32602b7a581b2610f3`. T10+ runtime production remains
LOCKED. Exact isolated candidate
`69593a19f56df3105a7b9657a76533e274e2eed6` passed its integration-owner
evidence review; it must be reconciled with the current integration-governance
head and rerun before integration. Fresh integrated evidence and independent
C2/C3/C4/C5/C6 review remain mandatory before approval.

T03 was the final legacy task grandfathered to finish directly on
`codex/havenline-sequential-task-01`. T04 and all later runtime work use
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

## Production Architecture V3 rule

For T10+ runtime activation, do not infer readiness from dependency status
alone. Run:

`python3 tools/havenline/production/architecture_v3.py readiness Txx`

Runtime implementation may begin only when the authoritative dependency state,
canonical packet/scope, ownership claim, and V3 capability feasibility all
permit it. External/hardware prerequisites marked `UNVERIFIED`, `UNAVAILABLE`,
`DEFERRED` or `MISSING_LOCAL` are not READY.

Use `critical_path_scheduler.py plan` to choose useful safe preparation and
ready work. The scheduler is advisory; it cannot grant ownership, unlock a task,
integrate a candidate or approve production.

Use `gate_fingerprint.py` for proof-reuse decisions. A matching fingerprint may
avoid a redundant deterministic rerun only when the registered reuse class
allows it. Heavy evidence marked `rebind_with_provenance` requires a bridge
record. Physical certification, critic review, integration, post-integration
regression, closeout and release remain exact-source/fresh. A prior FAIL can
never become a PASS through reuse.

Before integrating an isolated candidate, run a non-mutating
`synthetic_merge_forecast.py` against the current integration head and validate
any affected contract in `CONTRACT_REGISTRY.json`. A clean forecast does not
replace integration-owner review or fresh post-integration regression.

C0 consults `FAILURE_INTELLIGENCE.json` before repair. Historical matches are
advisory only: current evidence must independently confirm or reject the prior
root cause. Never auto-repair merely because a failure resembles an older one.

## Controlled parallel-production rule

Production flow is:

DEPENDENCY GRAPH -> V3 SCHEDULER/PREACTIVATION FEASIBILITY -> TASK PACKET ->
CLAIM DISJOINT PATHS -> BUILD ISOLATED -> CHEAP SENTINELS/SPECIALIST PREFLIGHTS ->
TEST -> PACKAGE CANDIDATE -> SYNTHETIC MERGE + CONTRACT FORECAST -> INTEGRATION
OWNER REVIEW -> RECONCILE STALE BASE -> INTEGRATE -> IMPACT REGRESSION -> FRESH
INTEGRATION EVIDENCE -> APPLICABLE CRITICS -> FIX/RETEST -> APPROVE -> UNLOCK
DEPENDENTS.

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

## Game Master owner accounts

`GAME_MASTER_POLICY.json` is a mandatory forward contract for T13, T33-T37,
T41-T43, T64-T66 and T70. It does not reopen T01-T08.

- Exactly two owner slots exist. Personal Google account identifiers stay out of public source.
- T43 binds both owner slots through verified Google Sign-In and proves the exact shipping package + release-signing OAuth identity, account switching and device/reinstall recovery.
- `GAME_MASTER` is permanent, owner-only and above public max VIP while inheriting all public VIP perks at maximum.
- All approved shop SKUs are zero-cost for Game Master accounts and normal-player prices remain unchanged.
- T13 owns `GM_CHALLENGE`, which is intentionally harder but selected only from the owner role—not from VIP, purchases or spend history.
- Game Master activity is separately tagged from normal revenue/F2P/purchase-fairness evidence and normal public competitive ranking.
- Candidate manifests for applicable tasks must include the `game_master_contract` proof block defined by `CANDIDATE_MANIFEST_TEMPLATE.json`; `closure_validator.py` rejects missing/stale Game Master proofs.

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

For simple status/continuity requests, do not turn progress reporting into a
retrieval loop. If the status is already answerable, answer it.

## Failure handling

Work through genuine failures: diagnose, preserve working checkpoints, change
approach when justified, fix and rerun. Do not lower thresholds to finish.
Record exact source/asset/capture hashes, tests, raw critic results, unresolved
defects and the next executable action after each cycle.

Every critic-driven repair must satisfy
`Docs/Production/ANTI_LOOP_ROOT_CAUSE_STANDARD.md`. Production defects require
causal production changes and unchanged matched-camera proof before another
critic run. Evidence-only changes cannot resolve them.

Before a repair, query `Docs/Production/FAILURE_INTELLIGENCE.json` through
`failure_intelligence.py` and give the matches to C0. A historical match is
never a diagnosis by itself; current evidence must confirm it. Record newly
verified reusable failure knowledge after closure so later tasks do not repeat
the same investigation.

Every retrieval/status investigation must satisfy
`Docs/Production/AGENT_EXECUTION_LOOP_GUARD.md`. Three consecutive retrievals
that add no material fact require immediate synthesis/stop; repeating equivalent
searches is prohibited.
