# Havenline frozen task packet — T09

Prepared: 2026-09-16T00:00:00Z

## Identity

- Task ID: T09
- Task name: Harvesting and automatic acquisition
- Workstream ID: `T09-harvesting-acquisition-builder`
- Owner: `harvesting-acquisition-builder`
- Isolated branch: `havenline/T09-harvesting`
- Reservation alias: `@reservation:T09`
- Exact pre-claim integration base: `7492074e40a0b061f31d8c32602b7a581b2610f3`

## Dependencies

- T06 is APPROVED at isolated source
  `47f86fae25b099abb5c7096c37ca7495453b2b8f`, integrated at
  `91f35f331aaabe2b1785b10c0d911f20da6f12d9`; its player action/contact contract
  is read-only.
- T07 is APPROVED at isolated source
  `0a30dc0859541626eb6aa9a9bb749abc93dcb355`, integrated at
  `94b3f6c5097356a3857ebd13a77fb1e316eb06ae`; it remains the sole action selector.
- T08 is APPROVED at exact integrated source
  `9d56ea8ae972d0a0705ff8b985e13fab31dde493`; preserve its 23-suite / 1535-check
  conservation, carrying and transfer closure.
- Stable interfaces: T06 contact markers/action progress, T07 canonical descriptor,
  simulation-owned gather events/counts and T08 source-to-actor transfer receipts.

## Frozen scope

Implement only T09-R01–T09-R12 in `Docs/Production/T09/FROZEN_SCOPE.md`.

## Path ownership

Owned production paths:

- `HavenlineGodot/assets/harvesting_v1/**`
- `HavenlineGodot/scripts/harvest_presentation.gd`
- `HavenlineGodot/tests/test_task09_harvesting.gd`
- `HavenlineGodot/tests/test_task09_integration.gd`
- `HavenlineGodot/tests/capture_task09_harvesting.gd`
- `Docs/Production/T09/**`
- `tools/havenline/task09/**`
- `.github/workflows/havenline-task09-*.yml`

Protected paths include all approved T01-T08 production paths, every GLB source,
the canonical registries and T06/T07/T08 modules. Integration-only paths include
`main.gd`, `simulation.gd`, `population_simulation.gd`, `outpost_simulation.gd`,
`outpost_view.gd` and `reference-contract.json`. Required foreign edits use a
structured change request.

## Acceptance gates

- G1-G9: REQUIRED.
- G10: REQUIRED for committed-event replay/duplication/tamper boundaries; T09 adds
  no premium economy.
- G11: REQUIRED for gameplay-scale adaptive-device readability and cancellation.
- G12-G14: REQUIRED.

## Resource / tool / actor / animation contract

- REQUIRED for T09.
- Resource registry SHA256:
  `8e9feba3a92972b10ac7dc8589e43bd0f988c2981ffe0fcace2edb1100e3bd9d`
- Actor capability matrix SHA256:
  `f319469be543267c6a21988d6b23f915550bd01c7d8513516b7410915680b1bf`
- Animation action matrix SHA256:
  `57df079f213a88e58b87e01aa7b520ca2fe4d98a41368307fdbba433a57d46e5`
- Reference manifest SHA256:
  `e271986bcbf319b7dd3c94bee0813e8cbd7caa4699781096c3f68e701f295d01`
- Resources to resolve/prove: `wood`, `stone`, `metal`, `fuel`.
- Introduced resources: none.
- Actor keys to prove: `player_lead`, `core_human_companion`,
  `rescued_survivor_helper`; only `player_lead` receives final T09 motion/tool
  presentation, while later owners retain distinct helper/survivor motion.
- Animation profiles to prove: `human_player_chop`, `human_player_mine`,
  `human_player_dismantle`.
- `animation_delta=true`; C5 is mandatory.
- Run `resource_actor_contract.py` against the exact candidate manifest.

## Game Master owner-account contract

- N/A for T09 under `GAME_MASTER_POLICY.json`; do not add owner role, VIP, shop,
  challenge or administration behavior.

## Required tests

- Universal baseline plus all approved T01-T08 impacted suites.
- `test_task09_harvesting`: registry/tool mapping, attachments, deterministic
  lifecycle, exact impact event, source-specific effects, depletion, pooling,
  invalid input and zero logical mutation.
- `test_task09_integration`: T07 selection, T06 motion/contact, T08 transfer/carry,
  cancellation, lead/hidden actor, exactly-once receipts, save/reload/migration/
  recovery and no new permanent control.
- Save-state matrix; six adaptive-device cases; source/resource contracts; C5
  full-motion coverage; component and integrated C6 records.

## Required evidence

- Exact base/candidate hashes and authorized changed-file manifest.
- All locked B harvesting pixels and relevant A acquisition pixels available to
  reviewers beside exact-source candidate frames/motion.
- Axe/pickaxe/salvage-pry turntables; gameplay front/rear/left/right/
  three-quarter/overhead/detail; phone/tablet/foldable and native 4K.
- Full real-time/slow chop, mine and dismantle cycles; entry/cancel/recovery;
  feet/toes/knees/hips/shoulders/elbows/hands/grip/tool/target/gear inspection.
- Wood/stone/metal/fuel approach-to-impact-to-T08-transfer sequences,
  conservation traces, depletion/respawn boundaries and pool/performance metrics.
- Raw independent C2/C3/C4/C5 inputs/outputs and deterministic C6 evidence.

## Required critics

- C2 — Technical / Visual Integrity Critic.
- C3 — Havenline Gameplay Identity Critic.
- C4 — Gameplay UX / Readability Critic.
- C5 — Motion / Rigging Critic.
- C6 — Performance Critic.

## Performance budget

- Assigned shares: characters/companions/NPCs plus production/interactables.
- Maximum visible equipped tools: one per presented harvesting actor.
- Maximum pooled source fragments: 32; maximum simultaneous impact pulses: 8.
- No added physics bodies; unchanged presentation state performs no node rebuild.
- Record draw/primitive/material/memory/frame-time deltas against the exact base.
- Physical-device native-4K/60 certification remains T68/T69.

## Candidate handoff

- Candidate commit/artifact/evidence: pending isolated build.
- Known failures: none before first build/test/capture.
- Unresolved mandatory defects: none recorded before first evidence cycle.
- Integration base: exact pre-claim authority
  `7492074e40a0b061f31d8c32602b7a581b2610f3`; candidate branch includes only
  the authorized shared governance claim prefix before builder changes.
- Integration-owner disposition: ASSIGNED; isolated construction is allowed only
  inside `@reservation:T09`.
