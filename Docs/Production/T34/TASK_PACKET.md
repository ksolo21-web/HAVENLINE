# T34 Task Packet — Server-authoritative premium economy

- Future branch: `havenline/T34-premium-economy`
- Future owner: `premium-economy-builder`
- Planned alias: `@reservation:T34`
- Dependencies: T14, T33
- Required critics: C3, C7, C8, C9

## Planned owned paths
- `HavenlineGodot/scripts/premium_economy_client.gd`
- `HavenlineGodot/data/premium_economy_contract_v1.json`
- `HavenlineGodot/tests/test_task34_premium_economy.gd`
- `HavenlineGodot/tests/test_task34_idempotency.gd`
- `Docs/Production/T34/**`
- `tools/havenline/task34/**`
- `.github/workflows/havenline-task34-*.yml`

## Game Master proof flags
`gm_entitlements_server_authoritative`, `gm_zero_cost_grants_idempotent_and_audited`.

## Required proof
client-trust rejection; replay/idempotency tests; audit trail semantics; recovery/migration; GM grant separation; normal-player value unchanged.
