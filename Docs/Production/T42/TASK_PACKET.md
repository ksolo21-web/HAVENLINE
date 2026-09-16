# T42 Task Packet — Privacy-respecting telemetry, difficulty analytics and crash diagnostics

- Future branch: `havenline/T42-telemetry-analytics`
- Future owner: `telemetry-analytics-builder`
- Planned alias: `@reservation:T42`
- Dependencies: T13, T14, T37, T41
- Required critics: C3, C7, C9

## Planned owned paths
- `HavenlineGodot/scripts/privacy_telemetry.gd`
- `HavenlineGodot/data/telemetry_schema_v1.json`
- `HavenlineGodot/tests/test_task42_telemetry.gd`
- `HavenlineGodot/tests/test_task42_redaction.gd`
- `Docs/Production/T42/**`
- `tools/havenline/task42/**`
- `.github/workflows/havenline-task42-*.yml`

## Game Master proof flags
`gm_analytics_separately_tagged`, `gm_revenue_conversion_excluded`.

## Required proof
schema allowlist; secret/identifier redaction; GM cohort separation; spend-blind analytics boundary; crash diagnostic usefulness; offline/failure behavior.
