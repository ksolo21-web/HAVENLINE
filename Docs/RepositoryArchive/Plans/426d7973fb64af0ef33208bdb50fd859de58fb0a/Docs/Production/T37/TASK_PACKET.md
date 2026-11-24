# T37 Task Packet — LiveOps Director

- Future branch: `havenline/T37-liveops-director`
- Future owner: `liveops-director-builder`
- Planned alias: `@reservation:T37`
- Dependencies: T12, T14, T33, T34
- Required critics: C3, C7, C8, C9, C10

## Planned owned paths
- `HavenlineGodot/scripts/liveops_director.gd`
- `HavenlineGodot/data/liveops_policy_v1.json`
- `HavenlineGodot/tests/test_task37_liveops.gd`
- `HavenlineGodot/tests/test_task37_rollback.gd`
- `Docs/Production/T37/**`
- `tools/havenline/task37/**`
- `.github/workflows/havenline-task37-*.yml`

## Game Master proof flags
`gm_liveops_admin_controls_server_authorized`, `gm_liveops_admin_actions_audited`.

## Required proof
server-time authority; schedule validation; rollback/kill switch; duplicate/idempotent execution; GM admin authorization/audit; normal-player isolation.
