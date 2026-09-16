# T18 Task Packet — Mechanized fishing, conveyors and helpers

- Future branch: `havenline/T18-mechanized-fishing`
- Future owner: `mechanized-fishing-builder`
- Planned alias: `@reservation:T18`
- Dependencies: T16, T17
- Required critics: C2, C3, C4, C6, C1

## Planned owned paths
- `HavenlineGodot/scripts/mechanized_fishing.gd`
- `HavenlineGodot/scripts/conveyor_system.gd`
- `HavenlineGodot/scripts/mechanized_fishing_helpers.gd`
- `HavenlineGodot/data/mechanized_fishing_v1.json`
- `HavenlineGodot/assets/production/t18_mechanized_fishing/**`
- `HavenlineGodot/tests/test_task18_mechanized_fishing.gd`
- `HavenlineGodot/tests/test_task18_integration.gd`
- `HavenlineGodot/tests/capture_task18_mechanized.gd`
- `Docs/Production/T18/**`
- `tools/havenline/task18/**`
- `.github/workflows/havenline-task18-*.yml`

## Mandatory forward contracts
`RESOURCE_TOOL_ACTOR_STANDARD.md`, `ACTOR_CAPABILITY_MATRIX.json`, `ANIMATION_ACTION_MATRIX.json` and current task-scope governance.

## Required proof
input/output conservation; conveyor jam/recovery tests; helper navigation and role-motion evidence; load/performance record; multi-angle production-line evidence.

## Start rule
Run `python3 tools/havenline/t13_t20/prepare_activation.py --task T18 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after dependencies clear, then apply the emitted reservation/claim and create/rebase the future branch.
