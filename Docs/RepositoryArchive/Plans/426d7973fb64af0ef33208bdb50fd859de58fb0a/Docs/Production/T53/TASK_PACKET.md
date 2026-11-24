# T53 Task Packet — Transportation and inter-region continuity

- Future branch: `havenline/T53-inter-region-transport`
- Future owner: `inter-region-transport-builder`
- Planned alias: `@reservation:T53`
- Dependencies: T43, T44, T45, T46, T47, T48, T49, T50, T51, T52
- Required critics: C1, C2, C3, C4, C6, C7

## Planned owned paths
- `HavenlineGodot/scripts/inter_region_transport.gd`
- `HavenlineGodot/data/transport_routes_v1.json`
- `HavenlineGodot/regions/transport/**`
- `HavenlineGodot/tests/test_task53_transport.gd`
- `HavenlineGodot/tests/capture_task53_transport.gd`
- `Docs/Production/T53/**`
- `tools/havenline/task53/**`
- `.github/workflows/havenline-task53-*.yml`

## Required proof
all-region route matrix; cargo/passenger conservation; save/reload mid-transition; cloud continuity; invalid-route rejection; camera/control readability; performance; multi-angle evidence.
