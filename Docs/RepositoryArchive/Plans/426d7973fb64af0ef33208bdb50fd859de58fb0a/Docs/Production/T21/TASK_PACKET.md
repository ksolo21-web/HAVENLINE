# T21 Task Packet — Visible hostiles, hunting and weapon progression

- Future branch: `havenline/T21-hostiles-hunting-weapons`
- Future owner: `combat-hunting-builder`
- Planned alias: `@reservation:T21`
- Dependencies: T06, T07, T08, T09, T13
- Required critics: C1, C2, C3, C4, C5, C6

## Planned owned paths
- `HavenlineGodot/scripts/hostile_director.gd`
- `HavenlineGodot/scripts/hunting_combat.gd`
- `HavenlineGodot/scripts/weapon_progression.gd`
- `HavenlineGodot/data/weapon_progression_v1.json`
- `HavenlineGodot/assets/combat/t21_weapons/**`
- `HavenlineGodot/assets/hostiles/t21/**`
- `HavenlineGodot/animations/combat/t21/**`
- `HavenlineGodot/tests/test_task21_combat.gd`
- `HavenlineGodot/tests/test_task21_integration.gd`
- `HavenlineGodot/tests/capture_task21_combat.gd`
- `Docs/Production/T21/**`
- `tools/havenline/task21/**`
- `.github/workflows/havenline-task21-*.yml`

## Mandatory forward contracts
`RESOURCE_TOOL_ACTOR_STANDARD.md`, `RESOURCE_ACTION_REGISTRY.json`, `ACTOR_CAPABILITY_MATRIX.json`, `ANIMATION_ACTION_MATRIX.json`, `TASK_SCOPE_OVERRIDES.json`, and the T13 spend-blind difficulty contract.

## Required proof
combat placeholder removal; contextual weapon selection; player/helper attack contact timing; hostile hit/reaction/death states; loot/carry conservation; weapon progression persistence; difficulty-input isolation; full motion-cycle closeups for hands/feet/weapon contact and clipping.

## Start rule
Run `python3 tools/havenline/t21_t32/prepare_activation.py --task T21 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after dependencies clear, then apply the emitted reservation/claim through the integration owner and create/rebase the future branch from the exact post-activation head.
