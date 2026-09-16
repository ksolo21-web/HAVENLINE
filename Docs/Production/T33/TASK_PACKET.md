# T33 Task Packet — Core economy & F2P progression model

- Future branch: `havenline/T33-core-economy-f2p`
- Future owner: `economy-f2p-builder`
- Planned alias: `@reservation:T33`
- Dependencies: T12, T17, T18, T19, T20, T32
- Required critics: C3, C7, C8, C9

## Planned owned paths
- `HavenlineGodot/scripts/economy_model.gd`
- `HavenlineGodot/data/economy_balance_v1.json`
- `HavenlineGodot/data/f2p_progression_v1.json`
- `HavenlineGodot/tests/test_task33_economy.gd`
- `HavenlineGodot/tests/test_task33_f2p.gd`
- `Docs/Production/T33/**`
- `tools/havenline/task33/**`
- `.github/workflows/havenline-task33-*.yml`

## Game Master proof flags
`gm_economy_separately_tagged`, `gm_excluded_from_f2p_population`.

## Required proof
zero-dollar progression simulation; source/sink conservation; no energy wall; spend-blind difficulty isolation; GM population exclusion; persistence/migration compatibility.
