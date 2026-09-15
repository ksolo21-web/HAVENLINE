# Havenline frozen task packet — T07

Prepared: 2026-09-15T13:10:00Z

## Identity

- Task ID: T07
- Task name: Havenline Simple Control & Context Director
- Workstream ID: wave2-context-director
- Owner: simple-control-context-builder
- Isolated branch: `havenline/T07-context-director`
- Exact runtime integration base: `91f35f331aaabe2b1785b10c0d911f20da6f12d9`

## Dependencies

- T04 is APPROVED at `e08fd37e9a999d878644c03089c4b4b253bd7472`.
- T06 is APPROVED at accepted isolated source
  `47f86fae25b099abb5c7096c37ca7495453b2b8f`, integrated at
  `91f35f331aaabe2b1785b10c0d911f20da6f12d9`.
- Preserve approved T01-T06 and their verified completion records.
- Stable interfaces: T04 camera/composition, simulation-owned movement/facing/
  outcomes, and T06 canonical action/progress motion selector.

## Frozen scope

Implement only T07-R01–T07-R12 in `Docs/Production/T07/FROZEN_SCOPE.md`.

## Path ownership

Owned production paths:

- `HavenlineGodot/scripts/context_director.gd`
- `HavenlineGodot/tests/test_task07_context_director.gd`
- `HavenlineGodot/tests/capture_task07_context_director.gd`
- `Docs/Production/T07/**`
- `tools/havenline/task07/**`
- `.github/workflows/havenline-task07-*.yml`

All approved T01-T06 runtime/assets are protected. `main.gd`,
`outpost_simulation.gd`, `outpost_view.gd` and `reference-contract.json` remain
integration-only and require a structured change request.

## Acceptance gates

- G1-G9: REQUIRED.
- G10: REQUIRED as a spend-blind/security-boundary proof even though T07 adds no
  economy or purchase system.
- G11-G14: REQUIRED.

## Resource / actor / animation contract

- REQUIRED for T07.
- Introduced resource IDs: none.
- Actor keys to prove: `player_lead`, `core_human_companion`,
  `rescued_survivor_helper`.
- Required new animation profiles: none; `animation_delta=false`.
- Context output must consume registered capabilities and remain compatible
  with the approved T06 body-motion/action-progress contract.
- Run `resource_actor_contract.py` against the exact candidate manifest.

## Required tests

- Universal baseline and all approved T01-T06 task regression suites.
- `test_task07_context_director` covering malformed/duplicate inputs, stable
  tie-breaks, priority, proximity, facing, capabilities, hysteresis, urgent
  preemption, movement cancellation, canonical output and no duplicate impacts.
- T04 camera/adaptive layout, T06 motion compatibility, population, save-state
  and phone/tablet/foldable matrices.
- Exact-source parser/resource checks and bounded C6 load/performance record.

## Required evidence

- Exact candidate/base hashes and authorized changed-file manifest.
- Machine-readable selection traces and tables for every ranking dimension,
  hysteresis boundary, cancel/reacquire path and role capability case.
- Continuous normal-speed evidence showing stable contextual focus, clear
  blocked/progress feedback and no permanent action controls.
- Gameplay-scale phone/tablet/foldable frames and native 3840×2160 scale-1.
- Raw independent C2, C3, C4 and C11 inputs/outputs plus deterministic C6.

## Required critics

- C2 — Technical / Visual Integrity Critic.
- C3 — Gameplay Systems Critic.
- C4 — UX / Accessibility Critic.
- C6 — Performance Critic.
- C11 — Accessibility / Input Critic.

## Performance budget

- Keep candidate evaluation bounded by an explicit nearby-candidate cap.
- Measure worst expected candidate population, switch frequency, allocations,
  process memory and shipping-scene frame/submission deltas.
- Any material regression against the exact integration base fails G8.
- Physical-device native-4K/60 certification remains T68/T69.

## Candidate handoff

- Candidate commit/artifact/evidence: pending isolated build.
- Known failures: none before first build/test/capture.
- Unresolved mandatory defects: none recorded before first evidence cycle.
- Reconcile status: governance-only assignment drift is permitted; runtime base
  is exact at `91f35f331aaabe2b1785b10c0d911f20da6f12d9`.
- Integration-owner disposition: ASSIGNED; isolated construction is allowed only
  inside `@reservation:T07`.
