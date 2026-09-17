# T14 Task Packet — Save-state/versioning foundation

- Future branch: `havenline/T14-save-versioning`
- Future owner: `save-versioning-builder`
- Planned alias: `@reservation:T14`
- Dependencies: T08, T10, T12
- Required critics: C2, C9
- Runtime build before activation: **FORBIDDEN**

## Planned owned paths
- `HavenlineGodot/scripts/save_versioning.gd`
- `HavenlineGodot/data/save_schema_v1.json`
- `HavenlineGodot/data/save_migrations_v1.json`
- `HavenlineGodot/tests/test_task14_save_versioning.gd`
- `HavenlineGodot/tests/test_task14_recovery.gd`
- `Docs/Production/T14/**`
- `tools/havenline/task14/**`
- `.github/workflows/havenline-task14-*.yml`

## Prepared builder handoff
Read these before implementing any T14 runtime code:

1. `Docs/Production/T14/FROZEN_SCOPE.md` — authoritative scope/exclusions.
2. `Docs/Production/T14/PREBUILD_CONTRACT.json` — dependency-independent preparation contract.
3. `Docs/Production/T14/T12_CONSUMER_BINDING.json` — prepared T12 consumer boundary; must be rebound at activation.
4. `Docs/Production/T14/IMPLEMENTATION_BLUEPRINT.md` — versioned envelope, adapter boundary, atomic write, backup/recovery, migration and transactional restore design.
5. `Docs/Production/T14/TEST_EVIDENCE_PLAN.md` — round-trip, migration, corruption, interruption, recovery, durability and critic matrices.
6. `Docs/Production/T14/ACTIVATION_CHECKLIST.json` — fail-closed activation sequence.
7. `Docs/Production/T14/defect-ledger.json` — preparation defect/blocker state.

## Dependency-interface rule
T14 must bind to the current approved T08/T10/T12 snapshot/restore interfaces at activation. It may not edit or work around a pre-T13 task to make a save test pass. If a required upstream interface is missing, unsafe, or changed, stop T14 activation and route the issue through the structured upstream interface/change process.

## Required proof
- schema-version fixture matrix;
- lossless approved-state round-trip proof;
- deterministic migration matrix;
- corruption validation/rejection matrix;
- deterministic atomic-write interruption matrix;
- migration interruption/retry proof;
- last-known-good backup recovery matrix;
- transactional restore / no-partial-success proof;
- rebound T08/T10/T12 adapter contract proof;
- repeated-cycle durability proof;
- exact-source C2/C9 evidence;
- all mandatory dimensions strictly >9.0 unrounded, target 10/10;
- zero unresolved mandatory defects.

## Activation start rule
Only after T08, T10 and T12 are all APPROVED/integrated and required ownership is released:

1. re-read exact current integration head;
2. rebind the current dependency interfaces and hashes without modifying those tasks;
3. recheck T14 planned path ownership;
4. refresh the generated packet/contracts and require zero preparation defects;
5. run `python3 tools/havenline/t13_t20/prepare_activation.py --task T14 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>`;
6. apply the emitted reservation/claim through the integration owner;
7. create/rebase `havenline/T14-save-versioning` from the exact post-activation head;
8. require candidate guard PASS before runtime/data expands.

Preparation artifacts do not grant activation by themselves.
