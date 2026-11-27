# Level 1 production floor

The fully purchased camp keeps the storehouse doors, furnace approach and both gates clear. The saw and quarry occupy the west work area. The cooker sits beside the north customer counter. Stock runs along the side and rear of those stations, with a separate staffed pickup at the counter. The character and survivor can reach every station from the central yard. The independent paid-floor review scored **9.5/10**. [Gameplay film](Paid-camp-surface-routes.mp4) · [Before-and-after floor map](../References/Reachable-workspace.jpg)

The second paid expansion opens 4.5 m of additional land along the west side. This gives the two workshops a utility wing while preserving the starter and first-expansion footprints.

## What changed on the ground

| Measure in the fully purchased camp | Build 11 | Build 12 |
| --- | ---: | ---: |
| Freight travel below ground, across eight routes | 48.51 m | 0 m |
| Total length across eight directed freight routes | 106.34 m | 54.60 m |
| Routes with a 180-degree fold at their end or approach | 4 | 0 |
| Connected floor accessible to the player | 128.56 m² | 183.70 m² |
| Connected floor with two player diameters of clearance | 100.30 m² | 146.59 m² |
| Widest usable passage into the counter's interaction area | 0.82 m | 2.32 m |

For the first three rows, the same paid save ran in the shipping scene from each build. The measurement clips each native 3D path segment at ground level and counts shared hardware for each material that travels along it. The access survey sampled the actual station interaction areas at 7.5 cm intervals with the character's 62 cm diameter. The independent survey found a 1.03 m approach at the saw, 1.43 m at the drill and 1.44 m at the cooker. [3D path measurements](Before-and-after.json) · [Build 11 floor survey](../References/b11-aisle-measurements.json) · [Build 12 floor survey](../References/build12-aisle-measurements.json)

The approved raised straight, corner and ramp pieces form the working deck. The lowest transfer surface sits 21.5 cm above the floor. The first visual review spotted a short dead end beside the cold dock. Its path had folded back through its own entrance. The corrected route leaves the warehouse mouth in the direction the adapter faces, with the steak visible on the first supported bend. [Original cold-dock review](First-visual-review/Cooker.jpg) · [Final untouched gameplay frame](Cold-dock-transit.jpg) · [Threefold pixel crop of that frame](Cold-dock-detail.png)

A separate capture paused exactly one ordinary freight transfer and rendered both ends of the real camera zoom range. In both views the steak occupies the same world coordinates at the cold socket. [1× native frame](Cold-dock-1x.jpg) · [2× native frame](Cold-dock-2x.jpg) · [Camera and parcel readings](Cold-dock-zooms.json)

After moving a paid saw, its wood input still ended at the saw's new socket. Returning it to its original position restored all eight directed connections. Buying the saw and drill from the older cooker-only checkpoint spent the exact displayed prices. The buyer could move from the saw to the quarry without losing part of the purchase to storehouse deposit. [Twenty geometry and access checks](Default-and-moved-surface-checks.json) · [Purchase receipts](Purchase-approaches.json) · [Idle production, customer sales and reconnection](Automation/README.md)

## Walking and reference review

Using real thumbstick inputs, the player walked 15.76 m from the starting court to the saw, then 22.58 m from the saw to the serving counter. The game registered both work faces. The stills at each arrival use the full 2× gameplay zoom. [On-foot film](Saw-and-counter-on-foot.mp4) · [Saw at 2×](wood-at-work-face.jpg) · [Serving counter at 2×](counter-at-work-face.jpg) · [Input and arrival measurements](Public-aisles.json)

The forester crossed five working routes. Storehouse to cooker was 5.47 m, cooker to counter 5.93 m, counter to storehouse 9.93 m, storehouse to saw 11.84 m, and saw to drill 7.37 m. All five routes reached their working spot and recorded zero obstructed steps. [Footstep checks](Forester-walks.json)

The owner footage at 9.5–14.5 seconds and 37.5–42.5 seconds shows productive stations on the edges and people working through the central space. The D01, D03, D05 and D06 sheets supplied the supported roller shapes, storage doors and docks, separate counter buffer and camp arrangement. These were the comparison points for the final camera review. [Owner footage](../References/Owner-A-productive-edges.jpg) · [Conveyor designs](../References/Conveyor-designs.jpg) · [Gameplay and reference comparison](../References/Camp-design-and-actual-field.jpg)

The floor comparison ran on `77bfef9f58f133824f0326a6b747c5a0ae9c4879`. The release binds the same floor scripts and assets at `6f35a670bac57a0002aa44b9abedbb257848fd30`. [Verified source differences](../References/Reviewed-revision.json) The capture uses Godot 4.7.2 and the ordinary Level 1 camera in `res://field_opening.tscn`. It ran from copied, guarded save profiles. The main clip is a 576 × 832 software-rendered observation at 12 captured frames per second. All six touch-driven waypoints were reached. Its camera switches from 1× to 1.78×, then back to 1×. [Raw actor and cargo positions](Journey.json) · [Source and shipping-scene identity](../Source/Reviewed-files.json)
