# Havenline Task 2 — locked map-spanning expandable river layout

## Status

This specification REOPENS Task 2. The previously accepted full-width lake is now historical evidence only because Kaleb explicitly changed the requirement: the water must be a **true river that runs from one end of the map to the other and remains part of expandable land throughout the game**.

Task 3 is LOCKED again. No Task 3 implementation may begin until this river version of Task 2 passes all mechanical checks and both independent critic roles at >=9.0 in every mandatory dimension, aiming for 10/10.

## Coordinate system and world extents

- `X` = west/east; negative X is west, positive X is east.
- `Z` = north/south; positive Z is north, negative Z is south.
- Current movement bounds remain `X = -14.2 .. +14.2`, `Z = -16.2 .. +16.2` unless a later approved expansion task changes them.
- Existing generated terrain scaffold is 62 x 62 world units, so its nominal edges are `X = -31 .. +31`, `Z = -31 .. +31`.
- **The river is authored across the full 62-unit terrain now**, even though only the current unlocked rectangle is playable today. Expansion reveals more bank/river segments; it must not replace or regenerate a disconnected river later.

## Locked river centreline

Use a smooth Catmull-Rom or equivalent C1-continuous spline through these exact world-space anchors, from west terrain edge to east terrain edge:

| Anchor | X | Z | Purpose |
|---|---:|---:|---|
| R0 | -31.0 | -8.6 | west terrain entry |
| R1 | -24.0 | -7.2 | first northward reach |
| R2 | -17.0 | -9.0 | first southward bend |
| R3 | -10.0 | -6.8 | broad northward bend |
| R4 | -3.0 | -8.7 | centre-west southward bend |
| R5 | +4.0 | -6.9 | centre-east northward bend |
| R6 | +11.0 | -8.5 | east-middle southward bend |
| R7 | +19.0 | -6.7 | final broad northward bend |
| R8 | +25.0 | -8.1 | settle toward outlet |
| R9 | +31.0 | -7.3 | east terrain exit |

This creates **five primary readable meander bends** across the full terrain while avoiding an exaggerated zigzag. Intermediate spline sampling must be fine enough that collision, terrain carving, water mesh and shoreline use the same curve without visible segment corners.

### Current unlocked-map crossing

Within the present `X = -14.2 .. +14.2` movement width, the river must enter from the west boundary and leave through the east boundary as one continuous channel. It must never terminate in a rounded lake end inside playable space.

## Locked width profile

The river is intentionally variable rather than a constant strip.

- Nominal open-water width: **3.8 units**.
- Minimum open-water width anywhere: **3.2 units**.
- Maximum normal width: **4.4 units**.
- Local bends may widen by at most **+0.35 units** on the outside bank, but total water width may never exceed **4.6 units** in the current region.
- Straighter reaches should trend toward **3.4–3.8 units**.
- Major bend apices should trend toward **4.0–4.4 units**.
- Width changes must be gradual over at least **4.0 world units** of centreline travel; no sudden necking or bulges.

The water mesh, wet/no-walk test, terrain channel and save-recovery logic must all derive from the same sampled centreline + half-width function. No separate approximations are allowed to drift apart.

## Riverbank cross-section

Measured perpendicular to the local centreline on both sides:

1. **Water channel:** half the local open-water width.
2. **Wet edge / shallow transition:** `0.30` unit beyond water on each bank.
3. **Sloped bank:** `0.70` unit horizontal run on each bank.
4. **Snow-bank crest / soft shoulder:** `0.45` unit on each bank.
5. **Build setback:** minimum `1.60` units from the snow-bank crest before permanent buildings/stations.

Total protected river corridor from water centreline to unrestricted permanent-building land is therefore approximately **4.35–4.70 units per side depending on local water width**, but traversal paths may approach closer where they remain dry and do not clip the bank.

Bank heights must remain stylized and readable rather than canyon-like. Use a gentle elevation change that clearly separates water from dry ground without creating impassable cliffs unless a later biome specifically requires them.

## Camp-side placement

The **main camp is on the NORTH bank** of the river in the current frozen region.

- Core camp/workfloor stays north of the protected river corridor.
- No permanent camp structure may sit inside the 1.60-unit build setback from the north snow-bank crest.
- The closest river-facing production/fishing interaction pads may use a dedicated reinforced river-work strip, but their walkable surfaces must remain dry and must not narrow the main bank route below the lane minimum below.
- River-facing machinery should visually address the water rather than floating on it or pretending the river is a pond.
- The old lake-centred staging is retired as the layout target; reusable approved assets may be repositioned later under their own task gates.

### Current north-bank land reserve

Because the river centreline stays around `Z ~= -6.7 .. -9.0` in the current region, preserve a **minimum 18.0-unit gross north-side span** from the closest protected river-corridor edge to the northern current movement boundary at every current-map X slice where practical. Small local deviations caused by curvature may not reduce the dry north-side traversable span below **16.5 units**.

This is the primary present-day camp/production/expansion side.

## South-bank land reserve

The south bank must remain real usable land, not a decorative sliver.

Within the current movement rectangle:

- Preserve **at least 4.5 units of continuously traversable dry south-bank depth** between the protected river corridor and the current south movement boundary.
- Target **5.0–6.5 units** through most of the current region.
- No bend may pinch the current south-bank traversal corridor below **4.5 units**.
- South-bank permanent construction is initially limited by progression, not by missing terrain. The geometry must already support future unlocks.

Beyond the present `Z=-16.2` boundary, the existing 62-unit terrain provides substantial additional south-side land for later expansion.

## Traversal lanes and future crossings

### Along-bank lanes

Maintain continuous dry travel lanes on BOTH banks:

- North-bank continuous lane: minimum **2.2 units** clear width.
- South-bank continuous lane: minimum **2.0 units** clear width.
- Preferred ordinary width: **2.6–3.2 units**.
- No tree, rock, fence, station, snowbank or invisible collider may reduce these below minimum.

### Cross-river movement

Do **not** add a permanent bridge in this Task 2 correction unless required to preserve an already-approved route. Instead, reserve three future bridge/crossing corridors in the terrain/placement mask so later progression can add crossings cleanly:

- West crossing reserve: centre near `X=-9.0`.
- Central crossing reserve: centre near `X=+1.5`.
- East crossing reserve: centre near `X=+10.0`.
- Each reserve is a **3.0-unit-wide no-permanent-obstruction corridor** measured along X around the nearest river normal.

These are reserved build zones, not functional bridges yet. Crossing gameplay belongs to a later approved task.

## Expandable-land behavior

The river is a persistent world backbone.

- The full R0→R9 spline exists from initial world creation/save version onward.
- Current progression exposes only the currently unlocked land around part of it.
- When land expands east, west, north or south, newly unlocked areas reveal the already-authored river/banks rather than creating a new disconnected water body.
- Expansion masks must be clipped against the river corridor so unlocks never convert water into ordinary buildable land.
- Future biome transitions may change bank materials, vegetation and water treatment, but the river's continuity and save identity must remain stable unless an explicit later design task approves a confluence, fork or termination.
- The river can connect to later biome waterways, but no later region may silently overwrite the current river seed/path identity.

## Save and simulation rules

- Save river-layout version: `river_v1_mapspan`.
- Old lake-era saves must migrate deterministically.
- Any actor found inside the new wet corridor loads onto the nearest reachable dry bank position, preferring its previous side of the river when known.
- Migration preserves inventory, carried resources, job/assignment state, rescued/recruited identities and progression state.
- No migration may teleport an actor across the river unless its previous side cannot be recovered safely.
- Resource nodes, approved trees and structures that would become submerged must be relocated to the nearest valid same-side dry position or explicitly rejected by migration validation; never silently delete economic state.

## Visual target

The river must look like a continuous natural river, not a stretched rectangular lake.

Required visible characteristics:

- five broad readable meanders rather than straight-line monotony;
- continuous water flow direction implied west→east by subtle current strokes;
- variable width without abrupt changes;
- clean stylized turquoise/blue water consistent with the reference-video palette;
- rounded sculpted snowbanks and gentle dry-ground shoulders;
- no repeated oval lake ends, no rectangular strip edges, no visible spline kinks;
- no water/terrain z-fighting, broad banding, seams, flooded approved trees or bank cracks;
- no primitive-looking placeholder materials;
- the river remains readable from the normal oblique gameplay camera and native 4K captures.

## Locked Task 2 acceptance measurements

Before Task 2 can be approved again, evidence must prove:

1. River centreline begins at or beyond `X=-31` and ends at or beyond `X=+31` in generated terrain data.
2. Current playable water crosses both `X=-14.2` and `X=+14.2` boundaries continuously.
3. Exactly five primary meander bends are visually readable across the full terrain plan; no unintended micro-zigzagging.
4. Open-water width stays `3.2 .. 4.6` units.
5. Current south-bank dry traversal depth never falls below `4.5` units.
6. Current north-side gross dry span never falls below `16.5` units.
7. Along-bank path clearance meets `2.2` north / `2.0` south minimums.
8. Water mesh, channel carving, collision/wet test and save recovery sample the same river function.
9. Migration preserves inventory and actor side where possible.
10. Three future crossing reserves remain free of permanent obstructions.
11. Approved T01 trees remain unchanged and no approved tree is flooded.
12. Full current regressions pass.
13. Fresh source-bound actual renders cover full river plan, both map-edge crossings, all five bends, north/south bank routes, close bank contacts, normal gameplay and native 3840x2160 scale-1 output.
14. Both independent critic roles pass every mandatory scoped dimension at >=9.0, target 10.0, with no unresolved mandatory defect.
15. No unfinished APK or user benchmark is requested.

## Scope lock

This is still **Task 2**. It does NOT authorize Task 3 fences/gates, Task 4 camera redesign, bridges, new customer systems, new character rig work, later biomes or unrelated feature work. Necessary migration, river collision/path masks, terrain carving, rendering and evidence tooling are in scope because the river cannot be a truthful Task 2 feature without them.

Characters 2–4 final rigging and review remain last. Physical phone/tablet sustained native-4K/60 remains a separate final release gate and cannot be inferred from Task 2 screenshots.
