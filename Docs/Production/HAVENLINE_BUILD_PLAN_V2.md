# HAVENLINE BUILD PLAN V2 — Controlled Parallel Production

**Authoritative production plan.** This plan supersedes `Docs/Production/Archive/SEQUENTIAL_REPAIR_PLAN.pre-v2.2026-09-11.md` for forward production governance. The archived plan remains byte-identical to the pre-migration source and is retained for audit/recovery.

## Current research and render requirements — 2026-11-27

Read the [current T01–T80 reference/render refresh](TASK_PLAN_REFRESH_2026-11-27.md) before new task implementation or review. Its [task-by-task crosswalk](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md) attaches current source observations, pinned GitHub renders, task-specific proof and next actions to all 80 requested IDs. T01–T70 retain their original definitions/dependencies; T71–T80 remain `SOURCE_NOT_FOUND` and are not invented work.

The newest observed Codex evidence is Build 11, game source `989edd9283148e9f712387fb937ea36038cbd9d2`; [exact receipt and limits](ReferenceRefresh/2026-11-27/LATEST_BUILD_EVIDENCE.json). Continue from the newer Codex foundation with current ownership and source identity. The migration checkpoint/table below is historical, not today's lifecycle: T01–T11 have historical completion records, while current candidates and seven preserved visual holds require scoped reconciliation. No old approval automatically passes new assets.

Use the selected GitHub renders as exact design inputs, with image/model/scene hashes and actual in-game comparisons. The ordinary critic floor remains ≥9.5; **the requested 9.9 match is attained only when every applicable reference-comparison dimension reaches ≥9.9**, all mandatory evidence passes, and stronger exact-10 C1 style/reference requirements remain satisfied. [Match rules and enforcement gaps](TASK_PLAN_REFRESH_2026-11-27.md#what-99-matching-means) prevent archive/static-art scores or stale validator passes from becoming runtime approvals.

## Migration checkpoint (historical snapshot)

- Integration branch remains `codex/havenline-sequential-task-01`; T03 is grandfathered to finish there because its runtime work was already integrated before this migration.
- T01 and T02 remain APPROVED at their recorded accepted sources. Their approvals are not revoked by the stricter forward score rule.
- T03 is APPROVED at accepted gameplay source `5df9726e0b1c33f0f8865385b1c49aca229fd461`.
- T04 is APPROVED at accepted gameplay source `e08fd37e9a999d878644c03089c4b4b253bd7472`.
- T05 is APPROVED at accepted gameplay source `fa6fa70f154f3757d22303522ca3f6de2c3d391f`; 18 suites / 1119 checks, 77 source-bound frames, strict C1+C2 PASS, C6 minimum 9.1, final pixel signoff and G1-G14 passed.
- T06 is APPROVED at accepted isolated source `47f86fae25b099abb5c7096c37ca7495453b2b8f`, integrated at `91f35f331aaabe2b1785b10c0d911f20da6f12d9`; 19 suites / 1345 checks, exact runtime-review identity, exhaustive motion/surface evidence, C1 9.42, C2 9.42, C5 9.31 and fresh C6 passed.
- T07 is APPROVED at accepted isolated source `0a30dc0859541626eb6aa9a9bb749abc93dcb355`, integrated at `94b3f6c5097356a3857ebd13a77fb1e316eb06ae`; 21 suites / 1441 checks, exact-source visual/device/save/performance evidence, C2 9.46, C3 9.68, C4 9.24, C6 9.53 and C11 9.18 passed.
- T08 is APPROVED at exact integrated source `9d56ea8ae972d0a0705ff8b985e13fab31dde493`; 23 suites / 1535 checks, 44/44 locked frames, both locked recordings, exact route/conservation evidence, C2 9.55, C3 9.48, C4 9.52 and C6 9.61 passed.
- T09 is APPROVED. Exact integrated source 5415d85838ecf4bea8b3c71662072670e61797a0 passed 17 suites / 1006 checks, 7/7 save cases, 6/6 device cases, 1193/1193 indexed hashes, G1-G14, and fresh independent C2/C3/C4/C5/C6 review with every mandatory dimension strictly above 9.0 and zero unresolved defects.
- T10 World Transformation Framework is APPROVED at exact integrated source `eba0107def258824549fb10d81785290d0c81d97`; fresh impacted regression passed 7 suites / 653 checks, 7/7 save cases, 216/216 device projections and 36/36 native-4K captures. C1/C2/C3/C4 passed on the current candidate, C6/C7 were preserved under critic-specific invalidation with audited invariant proof, minimum mandatory dimension 9.350213966238757, zero unresolved defects.
- T11 Camp construction and visual upgrade system is PREPARED on `havenline/T11-camp-construction` from T10 approval commit `87a4346eb33473c3723c7b7c1bbf1dd04dba9131`. T12+ remains dependency-gated.
- Forward PASS requires each applicable mandatory critic dimension to score **at least 9.5/10, unrounded**. Exactly 9.5 passes the numerical floor. Aim for 9.9 or better; 10/10 is the ideal. All mandatory gates must pass with zero unresolved mandatory defects. See [current score enforcement](#current-critic-score-enforcement).

## Permanent Havenline product contract

Havenline stays simple and immediately enjoyable. Its permanent gameplay language is:

**MOVE → AUTO-INTERACT → GATHER → VISIBLY CARRY → DELIVER → TRANSFORM → RESCUE → BUILD/UPGRADE → EXPLORE → DEFEND.**

Controls remain one primary movement joystick with auto collect, auto gather/harvest, auto attack, contextual unloading/deposit, contextual rescue/interactions, and only minimal deliberate-choice controls. Do not turn Havenline into button-heavy RPG combat, 4X warfare, complicated manual inventory, mandatory multiplayer, guild warfare, global free-text chat, unrestricted building, or an energy-wall game.

Launch remains Level 1–100 across a connected world, with practical visual progression every level, noticeable visual improvement at least every ~3 levels, major milestones approximately every 10 levels, spend-blind adaptive Challenge Director, seven companions (guardian dog, gray wolf, fox, owl, male lion, white tiger, brown bear), weather/day-night, survivor rescue/workers, production, defense, physical carrying, world transformation, monetization/VIP, LiveOps, security, adaptive phone/tablet/foldable support, and the existing final native-4K/60 physical-device target.

## Automatic resource / tool / actor / animation contract

`Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md` and its machine-readable registries are mandatory forward-governance inputs:

- `RESOURCE_ACTION_REGISTRY.json`
- `ACTOR_CAPABILITY_MATRIX.json`
- `ANIMATION_ACTION_MATRIX.json`
- `TASK_SCOPE_OVERRIDES.json`

No production resource may become valid without a registered acquisition method, appropriate tool/method, carry presentation, destination and applicable actor/animation proof. Any resource introduced by T44-T52 must be registered and resolved before the introducing region can become `INTEGRATION_READY`.

Human helpers and rescued survivors may gather, carry, deposit, build, repair, guard and attack when their registered role permits it, but they must use role-distinct authored work/combat motion rather than simply replaying the selected player's animation. Logical impacts remain synchronized to the same authoritative gameplay beat.

All seven animal companion tasks require species-appropriate motion. Combat-capable companions require species-specific attack animation; animals do not silently use human tools. T27 additionally requires authored owl flight, takeoff, landing, wing-clearance, aerial navigation and dive-attack proof.

The existing orbiting/swiveling placeholder gather/attack presentation is explicitly non-final: T09 owns removal/replacement of the gathering-side presentation, while T21 owns removal/replacement of the combat-side presentation and weapon progression. T06 and T59-T61 prove character-specific tool/weapon contact and motion compatibility.

This contract is fail-closed in task-packet generation and candidate closure. C5 Motion/Rigging becomes additionally mandatory for T09, T16, T19, T21 and T23, and for T44-T52 whenever a candidate introduces a new actor action or animation profile.

**Non-disruption:** T05 was already assigned before this contract. Its frozen scope is not expanded or invalidated. If a later harvesting/combat task requires a physical tool asset T05 did not author, the later task owns it within authorized paths or raises a structured change request.

## Monetization and LiveOps rules

No energy wall, mandatory payment, fake discount, hidden spend-based difficulty, or intentionally miserable F2P path. Challenge Director may never consume purchase history, VIP, or spend signals. Purchases retain advertised value. Use one primary premium currency. VIP is permanent and transparent. Level 1–100 must remain realistically completable at $0. Launch LiveOps includes The First Thaw, weekly gameplay and sale rotation, seasonal/holiday frameworks, server-authoritative time, automatic validated scheduling, pre-approved composition, and a remote kill switch.

## Controlled parallel-production model

The old pure serial model is replaced by:

**DEPENDENCY GRAPH → ISOLATED PARALLEL BUILD → CONTROLLED INTEGRATION → FULL IMPACT-BASED REGRESSION → APPLICABLE SPECIALIST CRITICS → FIX/RETEST → APPROVE → UNLOCK DEPENDENTS.**

Only the integration owner may integrate production candidates into the integration branch. Isolated builders may never self-approve production. No two active workstreams may own the same production path. Foreign-path needs become structured change requests. A stale candidate must reconcile to the current integration candidate, rerun affected tests, and recapture affected evidence before integration.

## Task states

`LOCKED → PREPARED → ASSIGNED → BUILDING_ISOLATED → BUILT_PENDING_DEPENDENCY → INTEGRATION_READY → INTEGRATING → UNDER_REVIEW → FIX_REQUIRED → APPROVED`, with `BLOCKED` available whenever a mandatory prerequisite cannot currently be satisfied. State changes require evidence; time passing never advances status.

## Universal gates

- **G1 Dependency — required upstream interfaces/approved prerequisites satisfied.**
- **G2 Path ownership — only authorized production paths changed.**
- **G3 Scope — frozen requirements addressed; no unauthorized scope added.**
- **G4 Build/import — no compile/import/parser/resource failure.**
- **G5 Functional — feature operates through required use states.**
- **G6 Regression — impacted approved work remains valid.**
- **G7 Evidence provenance — evidence is current, exact-source-bound and hashed.**
- **G8 Performance budget — CPU/GPU/memory/geometry/physics/animation/resource budgets respected.**
- **G9 Persistence — save/reload/migration/recovery works where applicable.**
- **G10 Security/economy — required for purchases, economy, LiveOps, cloud and competitive-value systems.**
- **G11 Accessibility/adaptive UI — required for player-facing controls/UI where relevant.**
- **G12 Critic coverage — every required critic has current complete evidence.**
- **G13 Score: each applicable mandatory dimension must score at least 9.5/10 unrounded; no averaging and no unresolved mandatory defect. Stricter named requirements still apply.**
- **G14 Integration — the merged integration candidate, not merely the isolated branch, passes affected regression.**

### Current critic score enforcement

This rule applies game-wide to new reviews, changed candidates and reapprovals, not just Level 1. The [critic matrix](CRITIC_MATRIX.json) records the inclusive floor. An individual 9.499 does not pass; an individual 9.5 passes the numeric floor only. Keep independence, exact-source evidence, all other gates, owner sign-off where required, and stricter exact-10 shipping-art and reference requirements. Historical approval receipts are preserved as recorded, and an active invalidation is not cleared by this change.

Some legacy validators and workflows still check the old numeric floor, including `validate_migration.py`. Their green result is not sufficient for a candidate to pass G13 or advance. Until those checks are migrated and boundary-tested, the integration owner must verify the raw required scores on the exact candidate against the current rubric before approval; missing scores fail closed. No task is unlocked and no automation is deployed by this policy update.

[T01–T11 production reconciliation against Codex Build 9](T01_T11_PRODUCTION_RECONCILIATION_2026-11-27.md)

## Production sequence

| ID | Production task | State at migration (historical) | Current research / render requirements |
|---|---|---|---|
| T01 | Reference snow-covered trees and forest framing | APPROVED | [T01 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t01) |
| T02 | Terrain, snow, warm work-floor and lakeshore | APPROVED | [T02 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t02) |
| T03 | Fences, gates and navigable work lanes | APPROVED | [T03 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t03) |
| T04 | Reference camera and automatic screen composition | APPROVED | [T04 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t04) |
| T05 | Production station and prop kit | APPROVED | [T05 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t05) |
| T06 | Character 1 complete movement/interactions | APPROVED | [T06 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t06) |
| T07 | Havenline Simple Control & Context Director | APPROVED | [T07 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t07) |
| T08 | Visible inventory, physical carrying and transfers | APPROVED | [T08 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t08) |
| T09 | Harvesting and automatic acquisition | APPROVED | [T09 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t09) |
| T10 | World Transformation Framework | APPROVED | [T10 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t10) |
| T11 | Camp construction and visual upgrade system | PREPARED | [T11 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t11) |
| T12 | Level 1–100 progression architecture | LOCKED | [T12 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t12) |
| T13 | Progressive Difficulty & spend-blind Challenge Director | LOCKED | [T13 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t13) |
| T14 | Save-state/versioning foundation | LOCKED | [T14 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t14) |
| T15 | Customer/NPC models, crowds and routing | LOCKED | [T15 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t15) |
| T16 | Fishing and initial food processing | LOCKED | [T16 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t16) |
| T17 | Customer service, physical payment and reinvestment | LOCKED | [T17 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t17) |
| T18 | Mechanized fishing, conveyors and helpers | LOCKED | [T18 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t18) |
| T19 | Wheat/additional food production | LOCKED | [T19 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t19) |
| T20 | Road and vehicle customer service | LOCKED | [T20 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t20) |
| T21 | Visible hostiles, hunting and weapon progression | LOCKED | [T21 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t21) |
| T22 | Working defensive structures | LOCKED | [T22 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t22) |
| T23 | Survivor rescue and basic survivor identity | LOCKED | [T23 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t23) |
| T24 | Guardian dog | LOCKED | [T24 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t24) |
| T25 | Gray wolf | LOCKED | [T25 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t25) |
| T26 | Fox | LOCKED | [T26 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t26) |
| T27 | Owl | LOCKED | [T27 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t27) |
| T28 | Male lion | LOCKED | [T28 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t28) |
| T29 | White tiger | LOCKED | [T29 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t29) |
| T30 | Brown bear | LOCKED | [T30 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t30) |
| T31 | Integrated companion jobs and population safety | LOCKED | [T31 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t31) |
| T32 | Complete frozen-region Level 1–10 production progression | LOCKED | [T32 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t32) |
| T33 | Core economy & F2P progression model | LOCKED | [T33 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t33) |
| T34 | Server-authoritative premium economy | LOCKED | [T34 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t34) |
| T35 | Store, billing and entitlement system | LOCKED | [T35 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t35) |
| T36 | Permanent VIP system | LOCKED | [T36 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t36) |
| T37 | LiveOps Director | LOCKED | [T37 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t37) |
| T38 | Automatic Event Composer & Validator | LOCKED | [T38 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t38) |
| T39 | The First Thaw launch event | LOCKED | [T39 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t39) |
| T40 | Weekly/seasonal/holiday/sales rotations | LOCKED | [T40 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t40) |
| T41 | Anti-cheat and economic-security foundation | LOCKED | [T41 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t41) |
| T42 | Privacy-respecting telemetry, difficulty analytics and crash diagnostics | LOCKED | [T42 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t42) |
| T43 | Identity, cloud continuity and recovery | LOCKED | [T43 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t43) |
| T44 | Connected forest region / approximately Levels 11–20 | LOCKED | [T44 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t44) |
| T45 | Connected desert region / approximately Levels 21–30 | LOCKED | [T45 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t45) |
| T46 | Connected underwater region / approximately Levels 31–40 | LOCKED | [T46 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t46) |
| T47 | Connected sky region / approximately Levels 41–50 | LOCKED | [T47 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t47) |
| T48 | Connected volcanic region / approximately Levels 51–60 | LOCKED | [T48 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t48) |
| T49 | Connected swamp region / approximately Levels 61–70 | LOCKED | [T49 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t49) |
| T50 | Connected ruins region / approximately Levels 71–80 | LOCKED | [T50 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t50) |
| T51 | Connected underground region / approximately Levels 81–90 | LOCKED | [T51 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t51) |
| T52 | Connected alien region / approximately Levels 91–100 | LOCKED | [T52 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t52) |
| T53 | Transportation and inter-region continuity | LOCKED | [T53 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t53) |
| T54 | Day/night, weather, [music, SFX and event coverage](#t54--music-sound-effects-and-event-coverage) | LOCKED (full-world); audio coverage required for Level 1 acceptance | [T54 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t54) |
| T55 | Accessibility and control customization | LOCKED | [T55 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t55) |
| T56 | Performance/Quality/Balanced/Battery player modes | LOCKED | [T56 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t56) |
| T57 | Basic shareable milestone system | LOCKED | [T57 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t57) |
| T58 | Phone/tablet/foldable functional acceptance | LOCKED | [T58 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t58) |
| T59 | Character 2 final rigging and motion review | LOCKED | [T59 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t59) |
| T60 | Character 3 final rigging and motion review | LOCKED | [T60 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t60) |
| T61 | Character 4 final rigging and motion review | LOCKED | [T61 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t61) |
| T62 | Complete Level 1–100 progression acceptance | LOCKED | [T62 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t62) |
| T63 | $0 lifelong-F2P player completion test | LOCKED | [T63 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t63) |
| T64 | Purchase-value/fairness test | LOCKED | [T64 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t64) |
| T65 | Full LiveOps launch rehearsal | LOCKED | [T65 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t65) |
| T66 | Security/exploit attack review | LOCKED | [T66 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t66) |
| T67 | Full-game reference/regression acceptance | LOCKED | [T67 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t67) |
| T68 | Sustained native 4K/60 phone evidence | LOCKED | [T68 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t68) |
| T69 | Sustained native 4K/60 tablet/foldable evidence | LOCKED | [T69 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t69) |
| T70 | Final production release handoff | LOCKED | [T70 requirements](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t70) |

Detailed dependencies and critic applicability are machine-authoritative in `DEPENDENCY_GRAPH.json` and `CRITIC_MATRIX.json`. Mandatory forward scope overlays for resource/tool/actor/animation behavior are machine-authoritative in `TASK_SCOPE_OVERRIDES.json` and the three contract registries. T01–T10 accepted records remain authoritative; T10 closure is recorded in `Docs/Production/T10/verified-completion.json`.

## T71–T80 — requested IDs without recovered source definitions

All ten rows remain explicit source gaps in the [current crosswalk](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t71) and the preserved [custody index](../RepositoryArchive/Plans/TASK_CUSTODY_T01_T80.md). They have no invented names, dependencies, assets or runtime assignments.

## T54 — Music, sound effects and event coverage

**T54 owns audio direction, music, ambience, sound effects (SFX), the cue register, mix and listening approval.** Every gameplay or UI task owns emitting accurate events and demonstrating coverage for the player-facing states it introduces. Apply this requirement to the active Level 1 playtest now; do not wait for full-world T54. This is a Level 1 acceptance requirement, not activation or approval of full-world T54 or a change to the production dependency graph. Later tasks extend the same register as their features enter scope.

### Required Level 1 coverage

| Event family | Gameplay owner(s) | Required audio coverage |
|---|---|---|
| App, menus and controls | T07, T55 | Boot/title, pause/resume, menu open/back, select/confirm/cancel, unavailable actions, settings and accessibility previews. |
| Snow, camp and movement | T01–T04, T06, T54 | Wind and visible water where applicable; camp versus snow footsteps and landings tied to contact; furnace ignition and proximity ambience; gate approach/open/close/latch, with clear camp-to-field transitions. |
| Harvest, carry and storage | T08, T09 | Equip/swing/contact/miss as applicable; tree fall and regrowth; distinct material families for wood, quarry stone and relevant ores; pickup, full bag, rejected pickup, first and last item of a transfer, and storage-full feedback. Batch rapid transfers rather than spamming one cue per unit. |
| Purchases, construction and placement | T10, T11 | Unaffordable/blocked action, partial contribution, committed purchase, construction start/reveal/upgrade, and preview/blocked/confirm/cancel for paid equipment placement. No success cue on a preview, failure or replay. |
| Machines and delivery | T05, plus the task owning a given route or upgrade | Start/run/stop, missing input, output ready/full, material transfer and stalls. Cover cooker, saw and drill separately; cover conveyor movement, blocked/full states and restart when the feature is in the candidate. |
| Customers, survivors and companions | T15, T17, T23, and the applicable companion task | Arrival/queue/service as applicable; order, physical meal handoff and committed payment each distinct; rescue, work, delivery and relevant species actions. Applies to the actual Level 1 slice without unlocking future features or introducing fish to Level 1. |
| Threats, combat, recovery and progression | T12, T13, T21, T22, T54 | Threat warning distinct from attack, actual hit, player hurt/low health, defeat/recovery, healing start/end, victory, milestone and level transition. Playback follows actual state, not animation or previews alone. |

**Music and ambience:** establish a recognizable Havenline theme with field/exploration, camp/warmth and active-threat states; define boot/menu, milestone/victory and defeat/recovery handling where used. Specify entry, exit, priority and transitions, including when not to restart a track. Layer wind, hearth and local mechanical or environmental ambience independently. Cover day/night, weather, new regions and other later states under T54 as they are introduced; do not require every event to change the music.

**Cue register:** for every player-facing event and variant, record its source task, real trigger/phase, SFX and music/ambience response (or deliberate reuse/silence with a reason), output controls, timing, priority, concurrency, visual equivalent when important, asset source/usage rights, and test evidence. Include start/stop, success/denial, cancellation, repeat, interruption and restore where applicable. Intentional batching or shared cues are allowed only when the outcome remains clear in play. A row with no disposition or proof is open; an existing cue name alone does not pass it.

**Acceptance on the exact signed Level 1 candidate:** run a continuous route with sound and muted; include rapid 50+ item transfers, simultaneous machines, threat and purchase cues under load, and interrupted/reloaded events. Verify no missing or double success sounds, no clipping or audible loop seams, and that combat warnings and payment confirmations are not masked. Verify persisted music, SFX and ambience controls and pause/resume, audio interruption, and output changes. Require independent listening on real Android phone speakers (Fold7 cover and inner modes) and headphones, with critical events readable on mute. Keep the signed build identity, event times, captured playback, reviewer verdict and open gaps together. Desktop and mixer receipts support integration but cannot substitute for listening. Apply the Level 1 critic floor of 9.5/10 to applicable audio criteria; do not average away a failed critical cue.

## Wave checkpoint after T10 approval

- **Completed A / T04** — approved camera/composition; preserve its accepted source.
- **Completed B / T05** — approved station/prop kit; preserve accepted source `fa6fa70f154f3757d22303522ca3f6de2c3d391f`.
- **Completed C / T06** — approved Character 1 motion/contact foundation; preserve accepted source `47f86fae25b099abb5c7096c37ca7495453b2b8f` and integrated source `91f35f331aaabe2b1785b10c0d911f20da6f12d9`.
- **Completed D / T07** — deterministic simple-control/context director is APPROVED; preserve accepted source `0a30dc0859541626eb6aa9a9bb749abc93dcb355` and integrated source `94b3f6c5097356a3857ebd13a77fb1e316eb06ae`.
- **Completed E / T08** — visible inventory, carrying and transfers is APPROVED at exact integrated source `9d56ea8ae972d0a0705ff8b985e13fab31dde493`; preserve its 23-suite / 1535-check closure, complete locked-reference review and strict C2/C3/C4/C6 approval.
- **Completed F / T09** — Exact integrated source 5415d85838ecf4bea8b3c71662072670e61797a0 passed 17 suites / 1006 checks, 7/7 save cases, 6/6 device cases, 1193/1193 indexed hashes, G1-G14, and fresh independent C2/C3/C4/C5/C6 review with every mandatory dimension strictly above 9.0 and zero unresolved defects.
- **Completed G / T10** — World Transformation Framework is APPROVED at exact integrated source `eba0107def258824549fb10d81785290d0c81d97`; preserve its verified completion, C1/C2/C3/C4 current-candidate passes, C6/C7 preservation proof, and fresh integrated regression.
- **Prepared H / T11** — Camp construction and visual upgrade system is PREPARED on `havenline/T11-camp-construction`; it may move to ASSIGNED before runtime construction. T12+ remains dependency-gated.
- **Workstream Q** — QA/automation/integration infrastructure only.

These workstreams may build in parallel only after T03 is APPROVED and the registry assigns disjoint path ownership. Integration remains serial and integration-owner-controlled.

## Evidence and review

Every frozen candidate package contains exact source/commit hashes, changed-file list, test logs, deterministic screenshots/videos, performance records, raw critic inputs/outputs, known failures and dispositions. Relevant visual evidence includes front, rear, left, right, 3/4, gameplay-scale, close detail, overhead, applicable day/night/weather, and native 3840×2160 scale-1. Motion tasks additionally require real-time and slow cycles, turns/transitions, feet/toes/knees/hands, gear and animal appendage/contact views. Save and device matrices run early rather than waiting for final release.

Applicable resource/tool/actor tasks must additionally prove actual tool contact, animation impact timing, carry/delivery behavior, role-distinct helper/survivor motion, and species-specific companion work/attack motion. The candidate manifest stores hashes for the resource/action, actor-capability and animation-action registries so stale or selectively bypassed contracts fail closure.

## Performance rule

A task can fail even when visually excellent if it consumes an unsustainable share of the full-game budget. Early performance evidence protects headroom but cannot certify physical performance. Only T68/T69 can certify sustained native internal >=3840×2160 at >=60 FPS on representative physical phone/tablet/foldable hardware under completed-game load.

## Post-launch roadmap — outside release-critical T01–T70

- more Level-100 activities.
- new event families.
- richer secrets.
- more companion cosmetics/interactions.
- controlled decoration zones.
- deeper survivor personality.
- expanded photo tools.
- asynchronous friends/Haven visits.
- community projects.
- optional future 2–4-player co-op.
- new regions/expansions.
- future level-cap increase only when meaningful new progression exists.

These are not Havenline 1.0 dependencies and must not leak into release-critical scope without a new approved plan revision.
