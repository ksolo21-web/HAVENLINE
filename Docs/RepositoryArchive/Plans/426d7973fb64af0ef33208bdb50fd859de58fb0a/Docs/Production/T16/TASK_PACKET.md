# T16 Task Packet — Fishing and initial food processing

- Future branch: `havenline/T16-fishing-food`
- Future owner: `fishing-food-builder`
- Planned alias: `@reservation:T16`
- Dependencies: T08, T09, T15
- Required critics: C2, C3, C4, C5, C6, C1

## Planned owned paths
- `HavenlineGodot/scripts/fishing_system.gd`
- `HavenlineGodot/scripts/food_processing.gd`
- `HavenlineGodot/data/fishing_recipes_v1.json`
- `HavenlineGodot/data/food_processing_v1.json`
- `HavenlineGodot/assets/production/t16_fishing/**`
- `HavenlineGodot/tests/test_task16_fishing.gd`
- `HavenlineGodot/tests/test_task16_integration.gd`
- `HavenlineGodot/tests/capture_task16_fishing.gd`
- `Docs/Production/T16/**`
- `tools/havenline/task16/**`
- `.github/workflows/havenline-task16-*.yml`

## Mandatory forward contracts
- `Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md`
- `Docs/Production/RESOURCE_ACTION_REGISTRY.json`
- `Docs/Production/ACTOR_CAPABILITY_MATRIX.json`
- `Docs/Production/ANIMATION_ACTION_MATRIX.json`
- `Docs/Production/TASK_SCOPE_OVERRIDES.json`

## Required proof
resource/action registry coverage; authored tool/action contact timing; visible carry/delivery conservation; processing-state determinism; C5 motion/rigging evidence and standard critic evidence.

## Start rule
Run `python3 tools/havenline/t13_t20/prepare_activation.py --task T16 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after dependencies clear, then apply the emitted reservation/claim and create/rebase the future branch from the exact post-activation head.
