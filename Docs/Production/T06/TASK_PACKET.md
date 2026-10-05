# Havenline frozen task packet — T06

Prepared: 2026-09-14T14:32:36Z

## Identity

- Task ID: T06
- Task name: Character 1 complete movement/interactions
- Workstream ID: wave1-character1
- Owner: character1-motion-builder
- Isolated branch: `havenline/T06-character1`
- Exact base integration commit: `f9d815a7d05c4e811d22d620c6b0c00c768ce6c5`

## Dependencies

- T03 is APPROVED at `5df9726e0b1c33f0f8865385b1c49aca229fd461`.
- Preserve approved T01-T05; T05 is accepted at
  `fa6fa70f154f3757d22303522ca3f6de2c3d391f`.
- Stable interfaces: simulation-owned position/facing/action progress, exact C1
  skeleton/source clips, T04 shipping camera, and current save/device contracts.

## Frozen scope

Implement only T06-R01–T06-R12 in `Docs/Production/T06/FROZEN_SCOPE.md`.

## Path ownership

Owned production paths:

- `HavenlineGodot/animations/c1/**`
- `HavenlineGodot/scripts/character1_motion.gd`
- `HavenlineGodot/tests/test_task06_character1.gd`
- `HavenlineGodot/tests/capture_task06_character1.gd`
- `Docs/Production/T06/**`
- `tools/havenline/task06/**`
- `.github/workflows/havenline-task06-*.yml`

Protected paths include every GLB and all approved T01-T05 runtime/assets.
Integration-only paths include `main.gd`, `outpost_simulation.gd`,
`outpost_view.gd` and `data/reference-contract.json`.

## Acceptance gates

- G1-G9: REQUIRED.
- G10: N/A; T06 changes no economy, entitlement, security, cloud or competitive
  value system.
- G11: REQUIRED for gameplay-scale adaptive-device visibility; no UI addition.
- G12-G14: REQUIRED.

## Resource / tool / actor / animation contract

- REQUIRED for T06.
- Resources resolved by T06: none; T09/T16/T19 own resource freezes.
- Actor keys to prove: `player_lead`, `core_human_companion`.
- Foundation profiles to prove: Character 1 locomotion and the T06-R04 contact
  body set, including compatibility for future `human_player_chop`,
  `human_player_mine` and attack/tool attachment without claiming T09/T21.
- `animation_delta=true`; C5 is mandatory.
- Run `resource_actor_contract.py` against the exact candidate manifest.

## Required tests

- Universal baseline and all T01-T05 approved-task regression suites.
- `test_task06_character1` for source immutability, clip/cycle/transition schema,
  normalized transforms, contact beats, role switching and no duplicate impacts.
- `test_motion_and_performance`, `test_population`, save-state matrix and full
  phone/tablet/foldable layout matrix.
- Exact-source import/parser/resource checks and C6 animation/performance record.

## Required evidence

- Exact candidate/base hashes and authorized changed-file manifest.
- Source C1 views and authoritative reference-video pixels where applicable.
- Front/rear/left/right/three-quarter/overhead; full real-time and slow cycles;
  start/stop/turn transitions; close feet/toes/knees/hips/hands/gear/contact.
- Player-lead and core-companion use states, slope and normal gameplay framing.
- Native 3840×2160 scale-1 evidence and performance metrics.
- Raw independent C1, C2 and C5 inputs/outputs plus deterministic C6.

## Required critics

- C1 — Reference Fidelity Critic.
- C2 — Technical / Visual Integrity Critic.
- C5 — Motion / Rigging Critic.
- C6 — Performance Critic.

## Performance budget

- Assigned subsystem: characters/companions/NPCs (22% global share).
- T06 target: one existing visible rig; zero added models/textures/materials and
  zero added physics bodies; bounded animation-library/storage growth.
- Any material regression versus the exact integration base fails G8.
- Physical-device native-4K/60 certification remains T68/T69.

## Candidate handoff

- Candidate commit/artifact/evidence: pending isolated build.
- Known failures: none before first build/render; source locomotion still needs
  T06-specific foot/knee/transition/contact proof.
- Unresolved mandatory defects: none recorded before first evidence cycle.
- Reconcile status: exact base is current integration head at assignment.
- Integration-owner disposition: ASSIGNED; isolated runtime construction allowed.
