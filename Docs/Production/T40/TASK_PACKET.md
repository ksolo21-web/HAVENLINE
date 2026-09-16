# T40 Task Packet — Weekly/seasonal/holiday/sales rotations

- Future branch: `havenline/T40-liveops-rotations`
- Future owner: `liveops-rotation-builder`
- Planned alias: `@reservation:T40`
- Dependencies: T38, T39
- Required critics: C3, C7, C8, C9, C10

## Planned owned paths
- `HavenlineGodot/scripts/liveops_rotation.gd`
- `HavenlineGodot/data/liveops_rotations_v1.json`
- `HavenlineGodot/tests/test_task40_rotations.gd`
- `Docs/Production/T40/**`
- `tools/havenline/task40/**`
- `.github/workflows/havenline-task40-*.yml`

## Required proof
schedule overlap matrix; server-time handling; validated sale/gameplay composition; F2P access; expiration/catch-up; rollback/kill switch; transparent prices.
