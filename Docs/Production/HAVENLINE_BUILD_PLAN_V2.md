# HAVENLINE BUILD PLAN V2

**Authoritative production plan.** This supersedes the pure-serial workflow model while preserving the archived pre-V2 plan at `Docs/Production/Archive/SEQUENTIAL_REPAIR_PLAN.pre-v2.2026-09-11.md` and its provenance record. It does **not** revoke T01/T02 approvals or restart T03.

## Current baseline
- Integration branch: `codex/havenline-sequential-task-01`.
- T01: APPROVED; accepted source/evidence remain authoritative.
- T02: APPROVED; accepted map-spanning river source/evidence remain authoritative.
- T03: active existing production work; migration may change planning/QA/critic/evidence infrastructure but may not silently expand T03 runtime scope.
- T04+ runtime implementation remains locked until T03 approval.
- Forward intermediate PASS requires **every applicable mandatory reviewed dimension >9.0 unrounded**, all applicable gates passing, and no unresolved mandatory defect. Target 10/10. This rule is not retroactive against T01/T02.

## Permanent Havenline product contract
`MOVE → AUTO-INTERACT → GATHER → VISIBLY CARRY → DELIVER → TRANSFORM → RESCUE → BUILD/UPGRADE → EXPLORE → DEFEND.`

One primary movement joystick. Auto collect, gather/harvest, attack, contextual unload/deposit and rescue/interactions. Minimal contextual controls only for genuine choices. No button-heavy RPG combat, 4X warfare, complicated manual inventory management, unrestricted building, mandatory guilds/guild warfare, free-text global chat, mandatory multiplayer or energy systems in Havenline 1.0.

Launch: Level 1–100; connected world; visible progression every level where practical; noticeable improvement at least every 3 levels; major milestone about every 10 levels; realistically completable; spend-blind Challenge Director; guardian dog, gray wolf, fox, owl, male lion, white tiger, brown bear; weather/day-night; survivor rescue/workers; production; defense; physical carrying; world transformation; monetization/VIP; launch/weekly/seasonal/holiday LiveOps; security; phone/tablet/foldable support; existing physical-device native-4K/60 acceptance contract.

Monetization: no energy wall, mandatory payment, hidden spend-based difficulty or fake discount; Challenge Director never consumes purchase/VIP/spend signals; purchases retain advertised value; one primary premium currency; VIP permanent/transparent; realistic $0 Level-1-to-100 completion; intentionally limited launch store.

LiveOps launch: The First Thaw; weekly gameplay event; weekly sale rotation; seasonal and holiday frameworks; server-authoritative time; automatic scheduling; pre-approved composition; automatic validation; remote kill switch.

## Production model
Old: `ONE TASK BUILDS → NEXT TASK BUILDS`.

New: `DEPENDENCY GRAPH → ISOLATED PARALLEL BUILD → CONTROLLED INTEGRATION → IMPACT-BASED REGRESSION → APPLICABLE SPECIALIST CRITICS → FIX/RETEST → APPROVE → UNLOCK DEPENDENTS`.

Only the integration owner may move production candidates onto the protected integration branch. A worker branch may become `INTEGRATION_READY`; it cannot self-declare production `APPROVED`.

### States
`LOCKED`, `PREPARED`, `ASSIGNED`, `BUILDING_ISOLATED`, `BUILT_PENDING_DEPENDENCY`, `INTEGRATION_READY`, `INTEGRATING`, `UNDER_REVIEW`, `FIX_REQUIRED`, `APPROVED`, `BLOCKED`.

### Universal gates
G1 Dependency; G2 Path ownership; G3 Scope; G4 Build/import; G5 Functional; G6 Regression; G7 Evidence provenance; G8 Performance budget; G9 Persistence; G10 Security/economy; G11 Accessibility/adaptive UI; G12 Critic coverage; G13 Score; G14 Integration.

**G13:** every applicable mandatory dimension must be **strictly >9.0 unrounded**. No averaging away a weak category. Target 10/10.

### Specialist critics
C1 Reference Fidelity; C2 Technical/Visual Integrity; C3 Havenline Gameplay Identity; C4 Gameplay UX/Readability; C5 Motion/Rigging; C6 Performance; C7 Progression/Difficulty; C8 Economy/Fairness; C9 Security/Exploit; C10 LiveOps; C11 Accessibility.

A builder cannot self-certify an independent critic pass. Use a genuinely separate $0 reviewer/model runtime when available and record provider/model, run/session ID, candidate hash, inputs and raw output. If unavailable, useful construction/testing continues but the independent critic gate remains BLOCKED.

## 70-task release sequence
T01 — Reference snow-covered trees and forest framing — APPROVED
T02 — Terrain, snow, warm work-floor and lakeshore — APPROVED
T03 — Fences, gates and navigable work lanes — ACTIVE
T04 — Reference camera and automatic screen composition
T05 — Production station and prop kit
T06 — Character 1 complete movement/interactions
T07 — Havenline Simple Control & Context Director
T08 — Visible inventory, physical carrying and transfers
T09 — Harvesting and automatic acquisition
T10 — World Transformation Framework
T11 — Camp construction and visual upgrade system
T12 — Level 1–100 progression architecture
T13 — Progressive Difficulty & spend-blind Challenge Director
T14 — Save-state/versioning foundation
T15 — Customer/NPC models, crowds and routing
T16 — Fishing and initial food processing
T17 — Customer service, physical payment and reinvestment
T18 — Mechanized fishing, conveyors and helpers
T19 — Wheat/additional food production
T20 — Road and vehicle customer service
T21 — Visible hostiles, hunting and weapon progression
T22 — Working defensive structures
T23 — Survivor rescue and basic survivor identity
T24 — Guardian dog
T25 — Gray wolf
T26 — Fox
T27 — Owl
T28 — Male lion
T29 — White tiger
T30 — Brown bear
T31 — Integrated companion jobs and population safety
T32 — Complete frozen-region Level 1–10 production progression
T33 — Core economy & F2P progression model
T34 — Server-authoritative premium economy
T35 — Store, billing and entitlement system
T36 — Permanent VIP system
T37 — LiveOps Director
T38 — Automatic Event Composer & Validator
T39 — The First Thaw launch event
T40 — Weekly/seasonal/holiday/sales rotations
T41 — Anti-cheat and economic-security foundation
T42 — Privacy-respecting telemetry, difficulty analytics and crash diagnostics
T43 — Identity, cloud continuity and recovery
T44 — Connected forest region / approximately Levels 11–20
T45 — Connected desert region / approximately Levels 21–30
T46 — Connected underwater region / approximately Levels 31–40
T47 — Connected sky region / approximately Levels 41–50
T48 — Connected volcanic region / approximately Levels 51–60
T49 — Connected swamp region / approximately Levels 61–70
T50 — Connected ruins region / approximately Levels 71–80
T51 — Connected underground region / approximately Levels 81–90
T52 — Connected alien region / approximately Levels 91–100
T53 — Transportation and inter-region continuity
T54 — Day/night, weather, audio and final game feedback
T55 — Accessibility and control customization
T56 — Performance/Quality/Balanced/Battery player modes
T57 — Basic shareable milestone system
T58 — Phone/tablet/foldable functional acceptance
T59 — Character 2 final rigging and motion review
T60 — Character 3 final rigging and motion review
T61 — Character 4 final rigging and motion review
T62 — Complete Level 1–100 progression acceptance
T63 — $0 lifelong-F2P player completion test
T64 — Purchase-value/fairness test
T65 — Full LiveOps launch rehearsal
T66 — Security/exploit attack review
T67 — Full-game reference/regression acceptance
T68 — Sustained native 4K/60 phone evidence
T69 — Sustained native 4K/60 tablet/foldable evidence
T70 — Final production release handoff

## Controlled parallel waves
While T03 is active: finish T03 plus governance/coordination/QA infrastructure only; do not implement T04+ runtime features.

After T03 APPROVED, Wave 1 may be assigned only after registry/path-collision validation:
- Workstream A — T04 camera/composition.
- Workstream B — T05 station/prop kit.
- Workstream C — T06 Character 1 motion.
- Workstream Q — QA/automation/integration infrastructure only.

No active workstreams may own overlapping production paths. Foreign-path needs become structured change requests under `Docs/Production/ChangeRequests/`.

## Integration owner procedure
Verify assignment, base commit, owned/protected paths and changed files; reconcile stale base; integrate into a clean candidate; run impact detection and required regression; capture fresh integration evidence; run applicable critics; fix/retest if any mandatory result <=9.0 or any gate fails; then and only then mark APPROVED, update registry and unlock dependents.

## Branching
The current production branch remains the protected integration branch unless explicitly migrated later. Isolated task branches use `havenline/TNN-short-name`, record exact base integration commit, and may not silently merge over newer integration work.

## Post-launch roadmap
More Level-100 activities; new event families; richer secrets; more companion cosmetics/interactions; controlled decoration zones; deeper survivor personality; expanded photo tools; asynchronous friends/Haven visits; community projects; optional future 2–4-player co-op; new regions/expansions; future level-cap increase only with meaningful new progression.

## Final release
T68/T69 alone certify sustained physical-device native internal >=3840×2160 at >=60 FPS where required. Emulator/software-renderer/native screenshots are not physical-device certification.
