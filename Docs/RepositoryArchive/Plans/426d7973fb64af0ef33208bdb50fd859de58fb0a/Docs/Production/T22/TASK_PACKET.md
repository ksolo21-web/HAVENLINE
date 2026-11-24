# T22 Task Packet — Working defensive structures

- Future branch: `havenline/T22-defensive-structures`
- Future owner: `defensive-structures-builder`
- Planned alias: `@reservation:T22`
- Dependencies: T11, T21
- Required critics: C1, C2, C3, C4, C6

## Planned owned paths
- `HavenlineGodot/scripts/defensive_structures.gd`
- `HavenlineGodot/data/defensive_structures_v1.json`
- `HavenlineGodot/assets/defense/t22_structures/**`
- `HavenlineGodot/tests/test_task22_defense.gd`
- `HavenlineGodot/tests/test_task22_integration.gd`
- `HavenlineGodot/tests/capture_task22_defense.gd`
- `Docs/Production/T22/**`
- `tools/havenline/task22/**`
- `.github/workflows/havenline-task22-*.yml`

## Required proof
build/upgrade transaction conservation; hostile interaction; damage/destroy/recovery states; navigation clearance; performance; persistence; multi-angle visual/use-state evidence.

## Start rule
Run `python3 tools/havenline/t21_t32/prepare_activation.py --task T22 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after T11/T21 clear.
