# T14 Task Packet — Save-state/versioning foundation

- Future branch: `havenline/T14-save-versioning`
- Future owner: `save-versioning-builder`
- Planned alias: `@reservation:T14`
- Dependencies: T08, T10, T12
- Required critics: C2, C9

## Planned owned paths
- `HavenlineGodot/scripts/save_versioning.gd`
- `HavenlineGodot/data/save_schema_v1.json`
- `HavenlineGodot/data/save_migrations_v1.json`
- `HavenlineGodot/tests/test_task14_save_versioning.gd`
- `HavenlineGodot/tests/test_task14_recovery.gd`
- `Docs/Production/T14/**`
- `tools/havenline/task14/**`
- `.github/workflows/havenline-task14-*.yml`

## Required proof
schema-version fixtures; migration/recovery matrix; corruption/interruption tests; approved-state round-trip proof; exact-source C2/C9 evidence.

## Start rule
Run `python3 tools/havenline/t13_t20/prepare_activation.py --task T14 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after dependencies clear, then apply the emitted reservation/claim and create/rebase the future branch from the exact post-activation head.
