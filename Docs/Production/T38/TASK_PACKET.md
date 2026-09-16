# T38 Task Packet — Automatic Event Composer & Validator

- Future branch: `havenline/T38-event-composer`
- Future owner: `event-composer-builder`
- Planned alias: `@reservation:T38`
- Dependencies: T37
- Required critics: C3, C7, C8, C9, C10

## Planned owned paths
- `HavenlineGodot/scripts/event_composer.gd`
- `HavenlineGodot/data/event_templates_v1.json`
- `HavenlineGodot/tests/test_task38_event_composer.gd`
- `HavenlineGodot/tests/test_task38_event_validation.gd`
- `Docs/Production/T38/**`
- `tools/havenline/task38/**`
- `.github/workflows/havenline-task38-*.yml`

## Required proof
schema rejection matrix; reward/economy bounds; deterministic composition; schedule conflicts; rollback metadata; kill-switch compatibility; no unvalidated activation.
