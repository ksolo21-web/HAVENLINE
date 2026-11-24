# T20 Task Packet — Road and vehicle customer service

- Future branch: `havenline/T20-road-vehicle-service`
- Future owner: `road-vehicle-service-builder`
- Planned alias: `@reservation:T20`
- Dependencies: T15, T17
- Required critics: C2, C3, C4, C6, C1

## Planned owned paths
- `HavenlineGodot/scripts/vehicle_customer_service.gd`
- `HavenlineGodot/scripts/vehicle_routing.gd`
- `HavenlineGodot/data/vehicle_customer_service_v1.json`
- `HavenlineGodot/assets/vehicles/t20_customers/**`
- `HavenlineGodot/tests/test_task20_vehicle_service.gd`
- `HavenlineGodot/tests/test_task20_integration.gd`
- `HavenlineGodot/tests/capture_task20_vehicle_service.gd`
- `Docs/Production/T20/**`
- `tools/havenline/task20/**`
- `.github/workflows/havenline-task20-*.yml`

## Required proof
vehicle route/queue determinism; vehicle-pedestrian separation; service/payment handoff continuity; save/reload queue recovery; multi-angle/performance evidence.

## Start rule
Run `python3 tools/havenline/t13_t20/prepare_activation.py --task T20 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after dependencies clear, then apply the emitted reservation/claim and create/rebase the future branch.
