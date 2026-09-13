# Havenline frozen task packet — T04

Generated: 2026-09-13T04:00:00Z

## Identity

- Task ID: T04
- Task name: Reference camera and automatic screen composition
- Workstream ID: wave1-camera
- Owner: camera-composition-builder
- Isolated branch: `havenline/T04-camera`
- Exact base integration commit: `5135cddf96123afb962f4046f41e5ac0e510428a`

## Dependencies

- T03 is APPROVED at gameplay source
  `5df9726e0b1c33f0f8865385b1c49aca229fd461`.
- Preserve the approved T01 forest, T02 terrain/river and T03 boundary/gates.
- Preserve `HavenlineGodot/data/reference-contract.json` unchanged.

## Frozen scope

Implement only the behavior in `Docs/Production/T04/FROZEN_SCOPE.md`.

## Path ownership

Owned production paths:

- `HavenlineGodot/scripts/camera_composition.gd`
- `HavenlineGodot/tests/test_task04_camera.gd`
- `HavenlineGodot/tests/capture_task04_camera.gd`
- `Docs/Production/T04/**`
- `tools/havenline/task04/**`
- `.github/workflows/havenline-task04-*.yml`

Protected/foreign-owned paths:

- Approved T01–T03 assets, scripts and records.
- All character GLBs.
- `HavenlineGodot/data/reference-contract.json`.

Integration-only paths:

- `HavenlineGodot/scripts/main.gd`
- `HavenlineGodot/scripts/outpost_simulation.gd`
- `HavenlineGodot/scripts/outpost_view.gd`

## Acceptance gates

- G1–G8: REQUIRED.
- G9: REQUIRED as save/lifecycle continuity regression; T04 adds no saved field.
- G10: N/A because T04 changes no security, entitlement or economy behavior.
- G11–G14: REQUIRED.

## Required tests

- Universal baseline suites.
- `test_task04_camera` deterministic composition suite.
- T01, T02 and T03 approved-task regression suites selected by impact analysis.
- Device matrix camera-scale, HUD-safe frame and resize/fold transitions.
- No new geometry, material, texture, physics, animation or storage increment.

## Required evidence

- Exact candidate and base hashes plus changed-file manifest.
- Source-bound landscape device-matrix gameplay frames and motion samples.
- Normal gameplay, action-target, directional-tracking, resize and condition
  views; disclosed diagnostics are supplemental.
- Actual checksum-bound reference pixels in every C1 review packet.
- Performance record and complete raw C1, C2 and C6 outputs.

## Required critics

- C1 — Reference Fidelity Critic.
- C2 — Technical / Visual Integrity Critic.
- C6 — Performance Critic.

## Performance budget

- Camera code adds no render content or physics/animation workload.
- Draw calls, primitives and visible materials must not materially regress from
  the accepted T03 scene under matched state/resolution.
- Physical 4K/60 certification remains deferred to T68/T69.

## Candidate handoff

- Candidate commit: pending
- Evidence package: pending
- Known failures: none before construction
- Unresolved mandatory defects: none before construction
- Integration wiring request: required for `HavenlineGodot/scripts/main.gd`
