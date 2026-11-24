# T05 post-completion visual repair scope — 2026-09-26

## Status

T05 mechanical/catalog/socket/layout contracts remain preserved from historical accepted source `fa6fa70f154f3757d22303522ca3f6de2c3d391f`, but visual approval is reopened by the 2026-09-26 post-completion audit.

The repair exists because the newly approved HAVENLINE reference language closes an old loophole: a custom authored GLB is **not** shipping-quality merely because it is not a Godot built-in primitive. If the final object still reads like a beveled box, cylinder, flat token, or dressed blockout at gameplay scale, it fails.

## Preserve exactly

- all T05 asset IDs;
- all catalog socket names and positions;
- catalog footprints and clearances;
- camp and lakeshore arrangement positions;
- later-task bindings;
- T03 routes, gates, collision and boundary authority;
- T04 camera/composition behavior;
- gameplay, economy, save, production and interaction logic.

## Approved art language

Use the user-approved visual references as the art-language authority:

- chunky sculpted silhouettes that remain readable on a phone;
- warm carved timber with visible grain/form breakup and layered construction;
- dark blue-gray metal with plates, brackets, rivets and purposeful hardware;
- orange/yellow heat or machinery accents;
- thick irregular snow that accumulates on forms and changes the silhouette;
- resource-specific authored geometry rather than generic stacks;
- faceted stone/ore/crystal nodes with snow contact;
- rope-bound logs with readable cut ends and bark;
- framed storage/resource platforms;
- bundled physical currency;
- shallow constructed timber/stone/metal camp tiles instead of flat UI markers.

No photorealism. No gritty realism. No generic low-poly blockout look.

## Repair order

1. **T05-R01 hearth/furnace** — rebuild the central production vessel first.
2. **T05-R07 resource props** — wood, stone/ore, metal, fuel, fish/food, money and crates.
3. **T05-R03 ground pads** — replace flat tokens with physical constructed camp platforms.
4. T05-R02 counters.
5. T05-R04 fishing fixtures.
6. T05-R05 processing fixtures.
7. T05-R06 defense fixtures.

## First repair batch acceptance

The first batch may change only T05-owned visual generator/assets/catalog hash/triangle/material metadata and matching T05 tests/evidence tooling as required.

It must preserve the exact socket and footprint contracts.

Before integration:
- deterministic generation/source integrity PASS;
- no primitive-looking/blockout visual finding;
- front/rear/left/right/three-quarter/detail evidence;
- normal gameplay-scale camp/lakeshore evidence;
- night/blizzard and native 3840x2160 scale-1 evidence;
- no floating/contact/clipping defect;
- C1/C2 every applicable mandatory dimension strictly >9.0 unrounded;
- C6 every mandatory dimension strictly >9.0;
- defects [];
- complete coverage and medium/high confidence.

Historical T05 scores do not close the reopened visual defects.
