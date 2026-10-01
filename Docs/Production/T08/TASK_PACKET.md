# Havenline frozen task packet — T08

Prepared: 2026-09-15T16:45:00Z

## Identity

- Task ID: T08
- Task name: Visible inventory, physical carrying and transfers
- Workstream ID: `T08-physical-inventory-builder`
- Owner: `physical-inventory-builder`
- Isolated branch: `havenline/T08-visible-inventory`
- Exact runtime integration base: `7744b9f6a063da3385ce10992ef732ba2c669890`

## Dependencies

- T05 is APPROVED at `fa6fa70f154f3757d22303522ca3f6de2c3d391f`;
  its authored resource-stack assets are read-only dependencies.
- T06 is APPROVED at accepted isolated source
  `47f86fae25b099abb5c7096c37ca7495453b2b8f`, integrated at
  `91f35f331aaabe2b1785b10c0d911f20da6f12d9`.
- T07 is APPROVED at accepted isolated source
  `0a30dc0859541626eb6aa9a9bb749abc93dcb355`, integrated at
  `94b3f6c5097356a3857ebd13a77fb1e316eb06ae`.
- Preserve approved T01–T07 and their verified completion records.
- Stable interfaces: simulation-owned inventory/events, T07 canonical actionable
  descriptor, T06 motion selector and T04 adaptive camera/composition.

## Frozen scope

Implement only T08-R01–T08-R12 in `Docs/Production/T08/FROZEN_SCOPE.md`.

## Path ownership

Owned production paths:

- `HavenlineGodot/scripts/carry_stack.gd`
- `HavenlineGodot/scripts/storage_stockpile.gd`
- `HavenlineGodot/scripts/transfer_feedback.gd`
- `HavenlineGodot/tests/test_task08_inventory.gd`
- `HavenlineGodot/tests/test_task08_integration.gd`
- `HavenlineGodot/tests/capture_task08_inventory.gd`
- `Docs/Production/T08/**`
- `tools/havenline/task08/**`
- `.github/workflows/havenline-task08-*.yml`

All approved T01–T07 assets/runtime remain protected. `main.gd`,
`simulation.gd`, `population_view.gd`, `outpost_simulation.gd`,
`outpost_view.gd` and `reference-contract.json` are integration-only and require
an approved structured change request.

## Acceptance gates

- G1–G9: REQUIRED.
- G10: REQUIRED for transfer replay/duplication/tamper boundaries; no premium
  economy is introduced.
- G11: REQUIRED for gameplay-scale readability and device adaptation.
- G12–G14: REQUIRED.

## Resource / actor / animation contract

- REQUIRED for T08.
- Resource registry SHA256:
  `b8912b83c724f7c52e2ad9ecc05786d483fcc9741aa9bf8db8c4e31d64d05df8`
- Actor capability matrix SHA256:
  `f319469be543267c6a21988d6b23f915550bd01c7d8513516b7410915680b1bf`
- Animation action matrix SHA256:
  `57df079f213a88e58b87e01aa7b520ca2fe4d98a41368307fdbba433a57d46e5`
- Reference manifest SHA256:
  `e271986bcbf319b7dd3c94bee0813e8cbd7caa4699781096c3f68e701f295d01`
- Current production resources presented: `wood`, `stone`, `metal`, `fuel`.
- Introduced resources: none.
- Required new actor capability or animation profile: none;
  `animation_delta=false`.
- `fish` and `wheat` remain visibly unready until T16/T19 freeze authored profiles.
- Run `resource_actor_contract.py` against the exact candidate manifest.

## Required tests

- Universal baseline and all approved T01–T07 impacted suites.
- `test_task08_inventory`: deterministic layouts, authored mappings, exact/mixed/
  compressed/huge counts, pool bounds, invalid inputs and no logical mutation.
- `test_task08_integration`: source/actor/destination routing, exactly-once receipts,
  lead/helper identity, build/repair transfers, save/reload/migration/recovery and
  T07/T06 compatibility.
- Save-state matrix, six device/layout cases, source/resource contracts and bounded
  C6 component plus integrated shipping-scene performance record.

## Required evidence

- Exact base/candidate hashes and authorized changed-file manifest.
- All 44 checksum-bound frames from both locked recordings available to reviewers;
  inspect the B carried-stack/camp-supply states and A source/carry/delivery states.
- Normal gameplay, front/rear/left/right/three-quarter/overhead and close/detail.
- Phone/tablet/foldable states and native 3840×2160 scale-1.
- Full normal-speed source→carry→destination sequences for player and helper;
  count/conservation, transfer direction, stack composition and pooling metadata.
- Raw independent C2/C3/C4 inputs/outputs and deterministic C6 evidence.

## Required critics

- C2 — Technical / Visual Integrity Critic.
- C3 — Havenline Gameplay Identity Critic.
- C4 — Gameplay UX / Readability Critic.
- C6 — Performance Critic.

## Performance budget

- Maximum visible carry pieces per actor: 48.
- Maximum visible destination pieces: 64.
- Maximum simultaneous transfer flights: 48.
- Component updates must be allocation-aware and unchanged-state updates must not
  rebuild nodes.
- Measure large-count update latency, pool reuse, retained nodes, memory, active
  flights and integrated draw/primitive/frame-time deltas.
- Physical-device native-4K/60 certification remains T68/T69.

## Candidate handoff

- Candidate commit/artifact/evidence: pending isolated build.
- Known failures: none before first build/test/capture.
- Unresolved mandatory defects: none recorded before first evidence cycle.
- Integration base is exact at `7744b9f6a063da3385ce10992ef732ba2c669890`.
- Integration-owner disposition: ASSIGNED; isolated construction is allowed only
  inside `@reservation:T08`.
