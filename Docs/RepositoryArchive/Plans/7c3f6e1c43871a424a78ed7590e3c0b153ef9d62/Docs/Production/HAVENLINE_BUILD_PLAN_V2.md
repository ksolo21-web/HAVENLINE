# HAVENLINE BUILD PLAN V2 — Controlled Parallel Production

**Authoritative production plan.** This plan supersedes `Docs/Production/Archive/SEQUENTIAL_REPAIR_PLAN.pre-v2.2026-09-11.md` for forward production governance. The archived plan remains byte-identical to the pre-migration source and is retained for audit/recovery.

## Migration checkpoint

- Integration branch remains `codex/havenline-sequential-task-01`; T03 is grandfathered to finish there because its runtime work was already integrated before this migration.
- T01 and T02 remain APPROVED at their recorded accepted sources. Their approvals are not revoked by the stricter forward score rule.
- T03 is APPROVED at accepted gameplay source `5df9726e0b1c33f0f8865385b1c49aca229fd461`.
- T04 is assigned as the next isolated workstream at `Docs/Production/T04/FROZEN_SCOPE.md`; T05+ remains locked until separately prepared and assigned.
- Forward intermediate PASS requires every applicable mandatory reviewed dimension to be **strictly > 9.0 unrounded**, every mandatory gate to pass, and zero unresolved mandatory defects. Target remains 10/10.

## Permanent Havenline product contract

Havenline stays simple and immediately enjoyable. Its permanent gameplay language is:

**MOVE → AUTO-INTERACT → GATHER → VISIBLY CARRY → DELIVER → TRANSFORM → RESCUE → BUILD/UPGRADE → EXPLORE → DEFEND.**

Controls remain one primary movement joystick with auto collect, auto gather/harvest, auto attack, contextual unloading/deposit, contextual rescue/interactions, and only minimal deliberate-choice controls. Do not turn Havenline into button-heavy RPG combat, 4X warfare, complicated manual inventory, mandatory multiplayer, guild warfare, global free-text chat, unrestricted building, or an energy-wall game.

Launch remains Level 1–100 across a connected world, with practical visual progression every level, noticeable visual improvement at least every ~3 levels, major milestones approximately every 10 levels, spend-blind adaptive Challenge Director, seven companions (guardian dog, gray wolf, fox, owl, male lion, white tiger, brown bear), weather/day-night, survivor rescue/workers, production, defense, physical carrying, world transformation, monetization/VIP, LiveOps, security, adaptive phone/tablet/foldable support, and the existing final native-4K/60 physical-device target.

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
| T04 | Reference camera and automatic screen composition | ASSIGNED / ACTIVE |
| T05 | Production station and prop kit | LOCKED |
| T06 | Character 1 complete movement/interactions | LOCKED |
| T07 | Havenline Simple Control & Context Director | LOCKED |
| T08 | Visible inventory, physical carrying and transfers | LOCKED |
| T09 | Harvesting and automatic acquisition | LOCKED |
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

Detailed dependencies and critic applicability are machine-authoritative in `DEPENDENCY_GRAPH.json` and `CRITIC_MATRIX.json`. T01–T03 accepted records remain authoritative; T04 scope is frozen in `Docs/Production/T04/FROZEN_SCOPE.md`.

## Parallel Wave 1 after T03 approval

- **Workstream A / `havenline/T04-camera`** — T04 camera/composition only.
- **Workstream B / `havenline/T05-props`** — T05 station/prop kit only.
- **Workstream C / `havenline/T06-character1`** — T06 Character 1 motion only; original C1 model is protected.
- **Workstream Q** — QA/automation/integration infrastructure only.

These workstreams may build in parallel only after T03 is APPROVED and the registry assigns disjoint path ownership. Integration remains serial and integration-owner-controlled.

## Evidence and review

Every frozen candidate package contains exact source/commit hashes, changed-file list, test logs, deterministic screenshots/videos, performance records, raw critic inputs/outputs, known failures and dispositions. Relevant visual evidence includes front, rear, left, right, 3/4, gameplay-scale, close detail, overhead, applicable day/night/weather, and native 3840×2160 scale-1. Motion tasks additionally require real-time and slow cycles, turns/transitions, feet/toes/knees/hands, gear and animal appendage/contact views. Save and device matrices run early rather than waiting for final release.

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
