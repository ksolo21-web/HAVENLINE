# T41 Task Packet — Anti-cheat and economic-security foundation

- Future branch: `havenline/T41-security-foundation`
- Future owner: `security-foundation-builder`
- Planned alias: `@reservation:T41`
- Dependencies: T14, T34, T35, T36, T37, T38
- Required critics: C9

## Planned owned paths
- `HavenlineGodot/scripts/security_client_guard.gd`
- `HavenlineGodot/data/security_contract_v1.json`
- `HavenlineGodot/tests/test_task41_security.gd`
- `HavenlineGodot/tests/test_task41_replay_tamper.gd`
- `Docs/Production/T41/**`
- `tools/havenline/task41/**`
- `.github/workflows/havenline-task41-*.yml`

## Game Master proof flags
`gm_role_authority_protected`, `gm_privileged_operations_server_authorized`.

## Required proof
client-trust rejection; save/clock/premium/VIP tamper tests; receipt/replay tests; privileged-command replay/parameter-tamper rejection; audit evidence; competitive isolation.
