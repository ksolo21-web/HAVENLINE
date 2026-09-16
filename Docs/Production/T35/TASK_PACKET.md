# T35 Task Packet — Store, billing and entitlement system

- Future branch: `havenline/T35-store-entitlements`
- Future owner: `store-entitlements-builder`
- Planned alias: `@reservation:T35`
- Dependencies: T34
- Required critics: C3, C7, C8, C9, C11

## Planned owned paths
- `HavenlineGodot/scripts/store_entitlements.gd`
- `HavenlineGodot/data/store_catalog_v1.json`
- `HavenlineGodot/tests/test_task35_store.gd`
- `HavenlineGodot/tests/test_task35_entitlements.gd`
- `HavenlineGodot/tests/capture_task35_store_ui.gd`
- `Docs/Production/T35/**`
- `tools/havenline/task35/**`
- `.github/workflows/havenline-task35-*.yml`

## Game Master proof flags
`all_shop_skus_zero_cost_for_gm`, `gm_claim_does_not_invoke_real_money_checkout`.

## Required proof
verified purchase boundary; duplicate/replay rejection; restore/recovery; transparent catalog; adaptive UI; GM zero-cost claim path; normal prices unchanged.
