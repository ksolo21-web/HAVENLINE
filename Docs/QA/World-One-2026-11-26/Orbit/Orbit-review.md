# Orbiting axe scale and the camp boundary

The axe is shorter and thinner at the actual following camera. The blade spans 41 × 32 px at the leftmost part of the orbit. The previous field showed 50 × 52 px at the same 1280 × 720 camera, location, pose and orbital phase. Both shots use the same regular wolf, facing the same direction. The smaller head still clears the character and remains readable against snow. [Before and after, with reference](Orbit-before-after.jpg) · [Screen coordinates, original model hashes and reference frames](Orbit-measurements.json)

## Measurements

The two B columns use the original 260 × 340 time-labeled cells from Alfred’s locked sheet. The two game columns use native 1280 × 720 gameplay pixels at 1×. Within each image I measured along and perpendicular to that image’s head-center-to-handle-end axis. The second source frame is diagonal. Comparing its axis-aligned screen rectangle directly would overstate blade size. The radius is the **screen-horizontal half-width** of the fitted path through nine source positions. The second axis is the projected screen-vertical half-height of that same ellipse. Those screen axes differ from the tool's local axes. [Locked original sheet](https://github.com/ksolo21-web/HAVENLINE/blob/b80c61f13ba31bb0940792dd47976a8e2878dbf5/Docs/Design/ResourceTurnarounds/2026-11-23-plots/sources/B-05.40-06.60-detail-sequence.png)

| Visible measure | B 5.80 s | B 6.10 s | Previous field | World One |
|---|---:|---:|---:|---:|
| Blade along / across shaft | 18.0 / 18.2 px | 22.5 / 21.6 px | 50.0 / 51.6 px | 41.3 / 32.1 px |
| Midshaft thickness | ~4 px | ~5 px | 18.5 px | 10.7 px |
| Head center to end of handle | 45.0 px | 39.7 px | 89.8 px | 73.9 px |
| Visible apparent hostile span | ~95.5 px | ~76.9 px | 132.9 px | 132.9 px |
| Starter screen-horizontal radius | ~75 px | ~75 px | 139.0 px | 130.7 px |
| Radius / hostile span | ~0.79 | ~0.98 | 1.05 | 0.98 |
| Head-center-to-butt / hostile span | ~0.47 | ~0.52 | 0.68 | 0.56 |

The two pale hostiles in B overlap. Their endpoints carry roughly 10–15 px of uncertainty. Blade and handle ends have roughly 2–4 px uncertainty and the thin shaft 1–2 px. The square-ish reference head and Havenline’s flared Meshy blade retain visibly different silhouettes. The final camera-to-wolf measurement uses a side-facing ordinary 2.4 m wolf. The larger boss has its own separate gameplay scale.

The starter projected ellipse has approximately 130.7 × 94.3 px radii, compared with 139.0 × 100.0 px before. The project uses 2.36 m along the camera-right ground axis and 2.64 m along the camera-near ground axis. Its 0.89-second period, one-to-three progression, 120° spacing and 1.23× upgraded radius are preserved. At a true 2× pinch, measured blade dimensions become 82.5 × 64.2 px, shaft thickness 21.4 px and radius 261.4 px. Tool and scenery enlarge together. The donor GLBs and their textures retain their bytes. Local scale of the displayed mesh is 0.64 across the original X blade axis, 0.83 along the original Y shaft and 0.50 along Z thickness, applied before the tool rotates.

## Contact and gate behavior

Actual swept contact uses the same transformed head vertices as the visible model. Three real tree hits and three real rock hits landed while circling targets at each of 30, 60 and 120 Hz physics. The upgraded three-head stationary contact test struck two separate hostile surfaces and depleted both. [Motion, boundary and mesh-contact results](Orbit-tests.json)

All 51 boundary checks passed. The center of the player’s feet on the paid fence line counts as inside. At both gate centers of all three paid footprints, all tool meshes and ribbons disappear on the line and remain hidden just inside. The turn clock pauses, contact history clears, and the full world tick emits no hero swing/equip/strike events. A first step four centimeters outside immediately shows the current one- or three-tool loadout. The unpaid clearing still permits harvesting.

The normal touch preflight recorded 14,926 successive 60 Hz samples. All 4,070 inside samples had an empty selected tool. All 10,856 exterior samples had the axe or pickaxe. Four sounds named swing during this particular early run originated from the watchtower shooting while the player’s turn counter remained fixed. That preflight used the older tower sound mapping. [Early full-route threshold trace](Natural-thresholds.json)


A fresh game with the current audio mapping reopened a copy of the genuinely earned full-route save. With the player placed inside and the normal enemy scheduler running, the paid watchtower fired three bolts and landed three hits. The running mixer selected its dedicated tower-fire and tower-hit WAVs. All 1,281 camp ticks kept the hero tool inactive and emitted no swing sound. [Current earned-save tower and player audio trace](Tower-audio-check.json)

## Axe scale against the gate, quarry and pine

Each ratio gives **previous field → World One** at the normal 1280 × 720 playing camera. A ratio of 0.50 means the tool measurement spans half of that object's projected extent. The blade is measured along and across its shaft at the left side of the orbit. Head-to-butt runs from the metal head's center to the end of the grip. The radius is the horizontal distance from the orbit center to its left edge.

| Projected environment feature | Feature at 1× | Blade along / feature | Blade across / feature | Head-to-butt / feature | Orbit radius / feature |
|---|---:|---:|---:|---:|---:|
| South gate, clear aperture | 114.1 px | 0.44 → 0.36 | 0.45 → 0.28 | 0.79 → 0.65 | 1.22 → 1.15 |
| East gate, clear aperture | 95.7 px | 0.52 → 0.43 | 0.54 → 0.34 | 0.94 → 0.77 | 1.45 → 1.37 |
| Starter stone bank, width | 52.8 px | 0.95 → 0.78 | 0.98 → 0.61 | 1.70 → 1.40 | 2.64 → 2.48 |
| Ordinary mature pine, width | 120.6 px | 0.41 → 0.34 | 0.43 → 0.27 | 0.74 → 0.61 | 1.15 → 1.08 |
| Same pine, height | 141.0 px | 0.35 → 0.29 | 0.37 → 0.23 | 0.64 → 0.52 | 0.99 → 0.93 |

At each paid gate the open leaves rotate 90°. Between their innermost collision faces the passage measures 2.26 m, within a 2.40 m hinge span. The two equally wide gates project differently because one runs along world X and the other along world Z. Each gate measurement follows the diagonal floor line crossing the opening. The same starter bank and pine projected to equal extents in both builds. The quarry width covers the visible seated stone mesh at `StarterResourceRock_stone_a`. The pine width and height cover its 5,952-vertex standing mesh at `ExteriorExactT01Visuals/SnowPine_WestA`. These figures describe that ordinary tree and that starter rock specifically.

The revised blade is roughly three fifths of the starter rock's width and just over a quarter of the mature pine's width. Its center-to-grip length still exceeds the width of that small quarry. I repeated both builds at the actual 2× gameplay zoom. All five comparison features and the axe dimensions doubled to within 0.002 px; every listed normalized ratio changed by less than 0.0001. Each object was centered separately using the same field-camera orientation and orthographic span. The gate and quarry values are comparisons between game builds. The locked source cells above establish the axe and wolf comparison. [Per-instance vertices, screen coordinates, gate endpoints, zooms and ratios](Environment-projection.json)
