# T05 integration change request

## Candidate

- Isolated branch: `havenline/T05-props`
- Candidate source: `8224596250e3cd37df2ea5cb3db3c9328108023c`
- Owned authority: `HavenlineStationKit` / `T05-station-kit-v1`
- Requested integration-only path: `HavenlineGodot/scripts/main.gd`

## Minimal shipping wiring

1. Preload `res://scripts/station_kit.gd` from `main.gd`.
2. Replace only the retired furnace and storage visuals at their unchanged
   `reference-contract.json` coordinates:
   - instantiate `hearth_vessel` as the existing `furnace` node so the accepted
     heat light and level-scale presentation still target the same node;
   - instantiate `cargo_crate` at the existing storage coordinate without
     changing storage interaction, inventory, prices or persistence.
3. Build a static-batched camp arrangement with `hearth_vessel` excluded to
   prevent duplicate geometry. Seat each placement with
   `OutpostSurface.height_at`.
4. Build the static-batched lakeshore arrangement at its catalogued world
   coordinates, also seated with `OutpostSurface.height_at`.

## Preserved contracts

- No edits to T01–T04 authorities or `reference-contract.json`.
- No production, fishing, transport, construction, customer, defense, economy,
  save, input, UI, character or animation behavior.
- Furnace and storage gameplay coordinates remain exact.
- T03 lanes and all three crossing reserves remain open by footprint tests.
- The T04 shipping camera is unchanged and must be used for integrated evidence.

## Required integration proof

- All existing suites plus `test_task05_station_kit` pass.
- Exact shipping-scene captures cover camp/lakeshore gameplay scale, route and
  gate visibility, day/night/blizzard, landscape device matrix, family detail
  views and three native 3840x2160 scale-1 frames.
- Integrated render metrics remain inside the T05 triangle, draw-call, material,
  texture, storage and zero-active-runtime-cost budgets.
- Manual contact-sheet quick look passes before C1, C2 or C6 is invoked.
