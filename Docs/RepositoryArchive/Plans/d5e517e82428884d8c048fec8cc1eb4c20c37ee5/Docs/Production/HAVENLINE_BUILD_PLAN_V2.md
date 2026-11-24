# HAVENLINE BUILD PLAN V2 — Controlled Parallel Production

**Authoritative production plan.** This plan supersedes `Docs/Production/Archive/SEQUENTIAL_REPAIR_PLAN.pre-v2.2026-09-11.md` for forward production governance. The archived plan remains byte-identical to the pre-migration source and is retained for audit/recovery.

## Migration checkpoint

- Integration branch remains `codex/havenline-sequential-task-01`; T03 is grandfathered to finish there because its runtime work was already integrated before this migration.
- T01 and T02 remain APPROVED at their recorded accepted sources. Their approvals are not revoked by the stricter forward score rule.
- T03 is APPROVED at accepted gameplay source `5df9726e0b1c33f0f8865385b1c49aca229fd461`.
- T04 is APPROVED at accepted gameplay source `e08fd37e9a999d878644c03089c4b4b253bd7472`.
- T05 is APPROVED at accepted gameplay source `fa6fa70f154f3757d22303522ca3f6de2c3d391f`; 18 suites / 1119 checks, 77 source-bound frames, strict C1+C2 PASS, C6 minimum 9.1, final pixel signoff and G1-G14 passed.
- T06 is APPROVED at accepted isolated source `47f86fae25b099abb5c7096c37ca7495453b2b8f`, integrated at `91f35f331aaabe2b1785b10c0d911f20da6f12d9`; 19 suites / 1345 checks, exact runtime-review identity, exhaustive motion/surface evidence, C1 9.42, C2 9.42, C5 9.31 and fresh C6 passed.
- T07 is APPROVED at accepted isolated source `0a30dc0859541626eb6aa9a9bb749abc93dcb355`, integrated at `94b3f6c5097356a3857ebd13a77fb1e316eb06ae`; 21 suites / 1441 checks, exact-source visual/device/save/performance evidence, C2 9.46, C3 9.68, C4 9.24, C6 9.53 and C11 9.18 passed.
- T08 is APPROVED at exact integrated source `9d56ea8ae972d0a0705ff8b985e13fab31dde493`; 23 suites / 1535 checks, 44/44 locked frames, both locked recordings, exact route/conservation evidence, C2 9.55, C3 9.48, C4 9.52 and C6 9.61 passed.
- T09 is ASSIGNED to `harvesting-acquisition-builder` on isolated branch `havenline/T09-harvesting` from exact integration base `7492074e40a0b061f31d8c32602b7a581b2610f3`; its frozen scope, packet and disjoint path reservation are authoritative. T10+ remains locked.
- Forward intermediate PASS requires every applicable mandatory reviewed dimension to be **strictly > 9.0 unrounded**, every mandatory gate to pass, and zero unresolved mandatory defects. Target remains 10/10.

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
- **G13 Score — every applicable mandatory dimension is strictly >9.0 unrounded; no averaging; no unresolved mandatory defect.**
- **G14 Integration — the merged integration candidate, not merely the isolated branch, passes affected regression.**

## Production sequence

| ID | Production task | State at migration |
|---|---|---|
| T01 | Reference snow-covered trees and forest framing | APPROVED |
| T02 | Terrain, snow, warm work-floor and lakeshore | APPROVED |
| T03 | Fences, gates and navigable work lanes | APPROVED |
| T04 | Reference camera and automatic screen composition | APPROVED |
| T05 | Production station and prop kit | APPROVED |
| T06 | Character 1 complete movement/interactions | APPROVED |
| T07 | Havenline Simple Control & Context Director | APPROVED |
| T08 | Visible inventory, physical carrying and transfers | APPROVED |
| T09 | Harvesting and automatic acquisition | ASSIGNED |
| T10 | World Transformation Framework | LOCKED |
| T11 | Camp construction and visual upgrade system | LOCKED |
| T12 | Level 1–100 progression architecture | LOCKED |
| T13 | Progressive Difficulty & spend-blind Challenge Director | LOCKED |
| T14 | Save-state/versioning foundation | LOCKED |
| T15 | Customer/NPC models, crowds and routing | LOCKED |
| T16 | Fishing and initial food processing | LOCKED |
| T17 | Customer service, physical payment and reinvestment | LOCKED |
| T18 | Mechanized fishing, conveyors and helpers | LOCKED |
| T19 | Wheat/additional food production | LOCKED |
| T20 | Road and vehicle customer service | LOCKED |
| T21 | Visible hostiles, hunting and weapon progression | LOCKED |
| T22 | Working defensive structures | LOCKED |
| T23 | Survivor rescue and basic survivor identity | LOCKED |
| T24 | Guardian dog | LOCKED |
| T25 | Gray wolf | LOCKED |
| T26 | Fox | LOCKED |
| T27 | Owl | LOCKED |
| T28 | Male lion | LOCKED |
| T29 | White tiger | LOCKED |
| T30 | Brown bear | LOCKED |
| T31 | Integrated companion jobs and population safety | LOCKED |
| T32 | Complete frozen-region Level 1–10 production progression | LOCKED |
| T33 | Core economy & F2P progression model | LOCKED |
| T34 | Server-authoritative premium economy | LOCKED |
| T35 | Store, billing and entitlement system | LOCKED |
| T36 | Permanent VIP system | LOCKED |
| T37 | LiveOps Director | LOCKED |
| T38 | Automatic Event Composer & Validator | LOCKED |
| T39 | The First Thaw launch event | LOCKED |
| T40 | Weekly/seasonal/holiday/sales rotations | LOCKED |
| T41 | Anti-cheat and economic-security foundation | LOCKED |
| T42 | Privacy-respecting telemetry, difficulty analytics and crash diagnostics | LOCKED |
| T43 | Identity, cloud continuity and recovery | LOCKED |
| T44 | Connected forest region / approximately Levels 11–20 | LOCKED |
| T45 | Connected desert region / approximately Levels 21–30 | LOCKED |
| T46 | Connected underwater region / approximately Levels 31–40 | LOCKED |
| T47 | Connected sky region / approximately Levels 41–50 | LOCKED |
| T48 | Connected volcanic region / approximately Levels 51–60 | LOCKED |
| T49 | Connected swamp region / approximately Levels 61–70 | LOCKED |
| T50 | Connected ruins region / approximately Levels 71–80 | LOCKED |
| T51 | Connected underground region / approximately Levels 81–90 | LOCKED |
| T52 | Connected alien region / approximately Levels 91–100 | LOCKED |
| T53 | Transportation and inter-region continuity | LOCKED |
| T54 | Day/night, weather, audio and final game feedback | LOCKED |
| T55 | Accessibility and control customization | LOCKED |
| T56 | Performance/Quality/Balanced/Battery player modes | LOCKED |
| T57 | Basic shareable milestone system | LOCKED |
| T58 | Phone/tablet/foldable functional acceptance | LOCKED |
| T59 | Character 2 final rigging and motion review | LOCKED |
| T60 | Character 3 final rigging and motion review | LOCKED |
| T61 | Character 4 final rigging and motion review | LOCKED |
| T62 | Complete Level 1–100 progression acceptance | LOCKED |
| T63 | $0 lifelong-F2P player completion test | LOCKED |
| T64 | Purchase-value/fairness test | LOCKED |
| T65 | Full LiveOps launch rehearsal | LOCKED |
| T66 | Security/exploit attack review | LOCKED |
| T67 | Full-game reference/regression acceptance | LOCKED |
| T68 | Sustained native 4K/60 phone evidence | LOCKED |
| T69 | Sustained native 4K/60 tablet/foldable evidence | LOCKED |
| T70 | Final production release handoff | LOCKED |

Detailed dependencies and critic applicability are machine-authoritative in `DEPENDENCY_GRAPH.json` and `CRITIC_MATRIX.json`. Mandatory forward scope overlays for resource/tool/actor/animation behavior are machine-authoritative in `TASK_SCOPE_OVERRIDES.json` and the three contract registries. T01–T08 accepted records remain authoritative; T08 closure is recorded in `Docs/Production/T08/verified-completion.json`.

## Wave checkpoint after T08 approval

- **Completed A / T04** — approved camera/composition; preserve its accepted source.
- **Completed B / T05** — approved station/prop kit; preserve accepted source `fa6fa70f154f3757d22303522ca3f6de2c3d391f`.
- **Completed C / T06** — approved Character 1 motion/contact foundation; preserve accepted source `47f86fae25b099abb5c7096c37ca7495453b2b8f` and integrated source `91f35f331aaabe2b1785b10c0d911f20da6f12d9`.
- **Completed D / T07** — deterministic simple-control/context director is APPROVED; preserve accepted source `0a30dc0859541626eb6aa9a9bb749abc93dcb355` and integrated source `94b3f6c5097356a3857ebd13a77fb1e316eb06ae`.
- **Completed E / T08** — visible inventory, carrying and transfers is APPROVED at exact integrated source `9d56ea8ae972d0a0705ff8b985e13fab31dde493`; preserve its 23-suite / 1535-check closure, complete locked-reference review and strict C2/C3/C4/C6 approval.
- **Assigned F / T09** — harvesting and automatic acquisition is ASSIGNED to `harvesting-acquisition-builder` on `havenline/T09-harvesting` from exact base `7492074e40a0b061f31d8c32602b7a581b2610f3`; build and review against its frozen packet are next.
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
