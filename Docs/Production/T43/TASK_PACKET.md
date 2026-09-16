# T43 Task Packet — Identity, cloud continuity and recovery

- Future branch: `havenline/T43-identity-cloud`
- Future owner: `identity-cloud-builder`
- Planned alias: `@reservation:T43`
- Dependencies: T14, T41
- Required critics: C9, C11

## Planned owned paths
- `HavenlineGodot/scripts/identity_cloud_continuity.gd`
- `HavenlineGodot/data/cloud_recovery_contract_v1.json`
- `HavenlineGodot/tests/test_task43_identity.gd`
- `HavenlineGodot/tests/test_task43_cloud_recovery.gd`
- `HavenlineGodot/tests/test_task43_account_switch.gd`
- `Docs/Production/T43/**`
- `tools/havenline/task43/**`
- `.github/workflows/havenline-task43-*.yml`

## Game Master proof flags
`google_sign_in_release_identity_proven`, `two_game_master_owner_slots_bound_server_side`, `account_switch_role_isolation_proven`, `reinstall_device_recovery_proven`.

## Required proof
release package/certificate OAuth identity; two verified subject-ID bindings server-side; account-switch isolation; sign-out/re-sign-in; reinstall/device recovery; failed/cancelled auth non-privileged state; forged local/email state rejection; client-artifact secret scan.
