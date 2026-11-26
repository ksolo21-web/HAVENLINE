# Furnace clearance and mineable stone banks

The focused captures below retain their original recording commits. The current playable version is `e978a44b1b112bb598f9ec1724b3616ec80e6970`. Its subsequent runtime change adjusted the backpack display. The geometry and mechanics measured here use the same source assets and implementation.

Integrated source `34df87a8195553c4636aa374ac3bfc11054a3bbd`, scene `HavenlineLevel1/field_opening.tscn`. The paired scene views isolate the landmark change against checkpoint `1a91281d514a62264f55f6df7aa6b17ece1a47ce`. The integrated joystick run used the same landmark and orbit logic. All seven measured gameplay-script checksums match the pinned commit. [Pinned gameplay source](https://github.com/ksolo21-web/HAVENLINE/tree/34df87a8195553c4636aa374ac3bfc11054a3bbd/HavenlineLevel1)

The revised stage-one furnace is **1.48 standing hero heights wide**, down from 1.95. Walking space across the center of the paid court increased from **3.75 to 4.93 furnace widths**. The court itself is the same size. The seated starter quarry now reaches the hero’s standing height, up from 0.59. The thinner hearth collider also opens a real walking lane. [Matched native before and after](Hearth-and-quarry-before-after.jpg) · [Measured coordinates, source hashes and collision checks](Measurements.json)

| Game-camera measure | World One checkpoint 1a91281d | Revised |
|---|---:|---:|
| Standing hero, hood to soles | 87.2 px | 87.2 px |
| Hearth projected width × height | 169.9 × 171.7 px | 129.1 × 130.5 px |
| Inner court width across the hearth foot | 636.8 px | 636.8 px |
| Hearth physical radius | 1.140 m | 0.866 m |
| Seated starter quarry width × height | 52.8 × 51.1 px | 89.7 × 86.8 px |
| Quarry width / standing hero height | 0.605 | 1.028 |
| Quarry height / standing hero height | 0.586 | 0.995 |
| Quarry width / ordinary pine width | 0.437 | 0.744 |
| Quarry height / ordinary pine height | 0.362 | 0.616 |

Widths are screen-horizontal and heights are screen-vertical. The hero measurement uses the posed, skinned character mesh. The pine is the same standing 5,952-vertex `SnowPine_WestA` in both scenes. The court measurement follows a horizontal projected floor line through the center of the furnace to the inside of the two 0.30 m palisade walls. The line describes the architectural space including the furnace footprint. A separate physics test swept the actual 0.31 m-radius player capsule north for four meters at X = 1.32 m. The old furnace stopped the player. The revised furnace cleared the full route.

At 2× zoom the objects cover twice as many pixels and retain the same proportions. Both 1280 × 720 landscape and 720 × 1280 portrait were tested. The comparison photos used independent diagnostic copies of earned progress, the same camera and a stage-one physical perimeter. A full paid camp can partly hide the quarry behind the south-west fence from this angle. The normal pre-purchase mining route independently exercised the bank before that wall existed. [Normal landscape](new-camp-landscape-1x.jpg) · [Normal portrait](new-camp-portrait-1x.jpg) · [2× landscape quarry](new-quarry-landscape-2x.jpg) · [2× portrait quarry](new-quarry-portrait-2x.jpg)

## Axe relative to the larger bank

| At the same leftmost orbital phase and 1× camera | Previous field 994ace86 | World One 1a91281d | Revised bank |
|---|---:|---:|---:|
| Blade width across shaft / quarry width | 0.98 | 0.61 | **0.36** |
| Blade length along shaft / quarry width | 0.95 | 0.78 | **0.46** |
| Head center to grip end / quarry width | 1.70 | 1.40 | **0.82** |
| Horizontal orbit radius / quarry width | 2.64 | 2.48 | **1.46** |

The polished axe maintains its 41.3 × 32.1 px blade, 73.9 px center-to-grip length and 130.7 px screen-horizontal orbit radius. The revised denominator is the visible 89.7 px-wide starter quarry. Evergreen and open gate measurements remain in the paired weapon report. [Pinned native axe screenshots, gate measurements and optical axes](../Orbit/Orbit-review.md)

## Comparison with recording B

At 8 s and 10 s the recording shows a narrow metal vessel above a broader ring of stones and coals. In 300-pixel-wide reductions of the locked frames, the upper vessel spans roughly 28–32 px, the lower ring 50–55 px, and the partly covered hero approximately 33–38 px. The bearing and cargo introduce several pixels of uncertainty. At 8 s, roughly 285–295 horizontal pixels of camp floor are visible at the height of the furnace apron. The frame crops the boundary, establishing about 5.2–5.9 ring widths of visible court as a lower-bound estimate. The revised game's 4.93 widths come closer to that spacing. The game retains the owner's original stone furnace model. Its outer stone silhouette is directly comparable to the broad base, while its upper silhouette differs from the recorded metal vessel. B28 corroborates the spatial separation between heater and stock. The locked frames contain no confidently identified mineable stone bank, so the 1.70× bank scale expresses the owner's readability preference. [Source stills at B8, B10 and B28](Locked-B-camp.jpg) · [Original recording-frame archive](https://github.com/ksolo21-web/HAVENLINE/tree/b80c61f13ba31bb0940792dd47976a8e2878dbf5/Docs/Production/T05/ReferenceFrames)

## Physical checks

Fresh profile on pinned 34df87a8, with unmodified game input and camera. The mine still shows the first strike after the bank begins shrinking. [Unpaid clearing](Played-clearing-34df87a8.png) · [Mining outside](Played-quarry-34df87a8.png) · [First wood payment](Played-payment-34df87a8.png) · [Earned hearth and snow](Played-hearth-34df87a8.png) · [Exact game and camera receipts](Played-route.json)

The field's ordinary joystick route landed three pickaxe hits at 7.600, 8.567 and 9.533 s. The third depleted the actual bank. The player collected all three stone drops. Near the player, the visible bank and its matching movement collider use the actual imported mesh triangles. Shrinking or depleting it updates movement and tool contacts. The far bank uses the same scale and retains its partially mined proportions across streaming. The independently rerun native regression on pinned source 34df87a8 passed all 11 checks covering full and damaged banks, collider and swept-triangle agreement, renewal and near/far transitions. Loose drops, carried stones and stockyard stones retain their own existing dimensions. [Runtime receipts](Measurements.json)
