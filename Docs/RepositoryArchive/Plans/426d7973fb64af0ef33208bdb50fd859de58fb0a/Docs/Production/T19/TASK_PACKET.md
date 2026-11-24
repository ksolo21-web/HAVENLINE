# T19 Task Packet — Wheat/additional food production

- Future branch: `havenline/T19-wheat-food`
- Future owner: `food-production-builder`
- Planned alias: `@reservation:T19`
- Dependencies: T16, T18
- Required critics: C2, C3, C4, C5, C6, C1

## Planned owned paths
- `HavenlineGodot/scripts/wheat_production.gd`
- `HavenlineGodot/scripts/food_production_extended.gd`
- `HavenlineGodot/data/wheat_food_v1.json`
- `HavenlineGodot/assets/production/t19_wheat_food/**`
- `HavenlineGodot/tests/test_task19_food_production.gd`
- `HavenlineGodot/tests/test_task19_integration.gd`
- `HavenlineGodot/tests/capture_task19_food.gd`
- `Docs/Production/T19/**`
- `tools/havenline/task19/**`
- `.github/workflows/havenline-task19-*.yml`

## Mandatory forward contracts
`RESOURCE_TOOL_ACTOR_STANDARD.md`, `RESOURCE_ACTION_REGISTRY.json`, `ACTOR_CAPABILITY_MATRIX.json`, `ANIMATION_ACTION_MATRIX.json`, `TASK_SCOPE_OVERRIDES.json`.

## Required proof
resource/action registry coverage; tool/helper contact timing; carry/delivery/transform conservation; production-line integration proof; C5 motion/rigging evidence and standard critic evidence.

## Start rule
Run `python3 tools/havenline/t13_t20/prepare_activation.py --task T19 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after dependencies clear, then apply the emitted reservation/claim and create/rebase the future branch.
