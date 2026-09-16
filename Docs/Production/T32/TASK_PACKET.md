# T32 Task Packet — Complete frozen-region Level 1–10 production progression

- Future branch: `havenline/T32-frozen-levels-1-10`
- Owner: `frozen-progression-builder`
- Alias: `@reservation:T32`
- Dependencies: T12, T13, T14, T16, T17, T18, T19, T20, T21, T22, T23, T31
- Critics: C1, C2, C3, C4, C6, C7

## Planned owned paths
- `HavenlineGodot/scripts/frozen_region_progression.gd`
- `HavenlineGodot/data/frozen_region_levels_1_10_v1.json`
- `HavenlineGodot/data/frozen_region_milestones_v1.json`
- `HavenlineGodot/tests/test_task32_levels_1_10.gd`
- `HavenlineGodot/tests/test_task32_integration.gd`
- `HavenlineGodot/tests/capture_task32_progression.gd`
- `Docs/Production/T32/**`
- `tools/havenline/task32/**`
- `.github/workflows/havenline-task32-*.yml`

## Required proof
complete deterministic Level 1–10 playthrough; progression cadence; resource/tool/actor/animation coverage; save/reload/migration; spend-blind difficulty; combat/defense/rescue/companion/customer/production integration; performance/regression; multi-angle use-state evidence.

## Start rule
Run T21–T32 activation preflight after all listed dependencies clear; reconcile the exact integration head and do not edit integration-only `main.gd`, `simulation.gd`, `population_simulation.gd`, `outpost_simulation.gd` or `outpost_view.gd` from the isolated builder.
