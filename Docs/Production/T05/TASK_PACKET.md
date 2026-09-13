# Havenline frozen task packet — T05

Generated: 2026-09-13T12:33:24Z

## Identity

- Task ID: T05
- Task name: Production station and prop kit
- Workstream ID: wave1-props
- Owner: station-prop-builder
- Isolated branch: `havenline/T05-props`
- Exact base integration commit: `746c3e8757ccaf2a279a6184b6ed109a143d5b3a`

## Dependencies

- T03 is APPROVED at gameplay source
  `5df9726e0b1c33f0f8865385b1c49aca229fd461`.
- T04 is APPROVED at gameplay source
  `e08fd37e9a999d878644c03089c4b4b253bd7472` and provides the shipping camera
  used for integrated T05 evidence.
- Preserve all approved T01–T04 assets, behavior and verified records.

## Frozen scope

Implement only T05-R01–T05-R12 in `Docs/Production/T05/FROZEN_SCOPE.md`.

## Path ownership

Owned production paths:

- `HavenlineGodot/assets/stations_v2/**`
- `HavenlineGodot/scripts/station_kit.gd`
- `HavenlineGodot/tests/test_task05_station_kit.gd`
- `HavenlineGodot/tests/capture_task05_station_kit.gd`
- `Docs/Production/T05/**`
- `tools/havenline/task05/**`
- `.github/workflows/havenline-task05-*.yml`

Protected/foreign-owned paths:

- Approved T01–T04 runtime paths and records.
- All character GLBs.
- `HavenlineGodot/data/reference-contract.json`.

Integration-only paths:

- `HavenlineGodot/scripts/main.gd`
- `HavenlineGodot/scripts/outpost_simulation.gd`
- `HavenlineGodot/scripts/outpost_view.gd`

## Acceptance gates

- G1–G8: REQUIRED.
- G9: REQUIRED as save/lifecycle continuity regression; T05 adds no saved field.
- G10: N/A because T05 changes no security, entitlement or economy behavior.
- G11: REQUIRED for automatic landscape camera/device readability; T05 adds no UI.
- G12–G14: REQUIRED.

## Required tests

- Universal baseline suites.
- `test_task05_station_kit` catalog, asset, material, socket, bounds, clearance,
  deterministic construction and performance-contract suite.
- T01–T04 approved-task regressions selected by impact analysis.
- Device-matrix gameplay composition for camp and lakeshore arrangements.
- Route-clearance checks against all affected T03 gates and work lanes.
- No save-schema change and no new active physics, animation or population load.

## Required evidence

- Exact candidate/base hashes and changed-file manifest.
- Source-bound multi-angle station-family gallery and close details.
- Normal gameplay-scale camp/lakeshore use arrangements, bright/day, night and
  blizzard conditions, device-matrix views and native-4K scale-1 frames.
- Actual checksum-bound reference pixels in every C1 packet.
- Quick-look contact sheet before critics, quantitative C6 record, and complete
  raw C1/C2 outputs with defect dispositions.

## Required critics

- C1 — Reference Fidelity Critic.
- C2 — Technical / Visual Integrity Critic.
- C6 — Performance Critic.

## Performance budget

- Assigned subsystem: production/economy/interactables (18% global share).
- Nominal visible T05 arrangement: at most 180,000 triangles, 48 draw calls,
  12 visible materials, 96 MiB unique texture memory and 15 MiB storage delta.
- T05 adds zero active physics bodies, skeletons, animations or population.
- Any material regression versus the accepted T04 scene fails G8 even when the
  absolute cap is not exceeded.
- Physical 4K/60 certification remains T68/T69.

## Candidate handoff

- Candidate commit: pending isolated build
- Candidate artifact hash: pending
- Evidence package: `Docs/Production/Evidence/T05/` plus source-bound CI artifact
- Known failures: none at assignment; baseline and reference audit pending
- Unresolved mandatory defects: none recorded before first render
- Reconcile status: exact base equals current integration head at assignment
- Integration-owner disposition: ASSIGNED; isolated runtime construction allowed

