# T17 Task Packet — Customer service, physical payment and reinvestment

- Future branch: `havenline/T17-customer-service`
- Future owner: `customer-service-builder`
- Planned alias: `@reservation:T17`
- Dependencies: T15, T16
- Required critics: C2, C3, C4, C6

## Planned owned paths
- `HavenlineGodot/scripts/customer_service.gd`
- `HavenlineGodot/scripts/reinvestment_loop.gd`
- `HavenlineGodot/data/customer_service_v1.json`
- `HavenlineGodot/tests/test_task17_customer_service.gd`
- `HavenlineGodot/tests/test_task17_integration.gd`
- `HavenlineGodot/tests/capture_task17_service.gd`
- `Docs/Production/T17/**`
- `tools/havenline/task17/**`
- `.github/workflows/havenline-task17-*.yml`

## Required proof
queue-to-service lifecycle; physical payment conservation; reinvestment-state proof; save/reload continuity; exact-source critic evidence.

## Start rule
Run `python3 tools/havenline/t13_t20/prepare_activation.py --task T17 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after dependencies clear, then apply the emitted reservation/claim and create/rebase the future branch.
