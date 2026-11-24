# T23 Task Packet — Survivor rescue and basic survivor identity

- Future branch: `havenline/T23-survivor-rescue`
- Future owner: `survivor-system-builder`
- Planned alias: `@reservation:T23`
- Dependencies: T06, T07, T14, T21
- Required critics: C1, C2, C3, C4, C5, C6

## Planned owned paths
- `HavenlineGodot/scripts/survivor_system.gd`
- `HavenlineGodot/scripts/survivor_jobs.gd`
- `HavenlineGodot/data/survivor_profiles_v1.json`
- `HavenlineGodot/assets/survivors/t23/**`
- `HavenlineGodot/animations/survivors/t23/**`
- `HavenlineGodot/tests/test_task23_survivors.gd`
- `HavenlineGodot/tests/test_task23_integration.gd`
- `HavenlineGodot/tests/capture_task23_survivors.gd`
- `Docs/Production/T23/**`
- `tools/havenline/task23/**`
- `.github/workflows/havenline-task23-*.yml`

## Mandatory forward contracts
`RESOURCE_TOOL_ACTOR_STANDARD.md`, `ACTOR_CAPABILITY_MATRIX.json`, `ANIMATION_ACTION_MATRIX.json`, `TASK_SCOPE_OVERRIDES.json`, save/versioning and T21 combat interfaces.

## Required proof
rescue/use-state lifecycle; identity persistence; gather/carry/deposit/build/repair/guard/heal/attack capability matrix; survivor-distinct work/combat motion; tool/weapon contact timing; population safety boundaries.

## Start rule
Run `python3 tools/havenline/t21_t32/prepare_activation.py --task T23 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after dependencies clear.
