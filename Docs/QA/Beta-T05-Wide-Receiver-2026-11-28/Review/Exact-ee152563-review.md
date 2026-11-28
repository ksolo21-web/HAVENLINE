# Havenline T05 wide receiver and owl review

The independently reviewed candidate `ee15256302784e8202bb28af910d076051043a21` is based on `65a9392f1f8af94f0ff18aa345c9b220a80def5c`. The changed gameplay criteria below meet the owner's 9.9 minimum. Scores apply to each stated dimension. The encounter gate is a separate pass. [Exact source and frame receipts](Exact-ee152563-review.json) · [Reference measurements and decisions](../References/Measurements.md)

| Applicable dimension | Score or result |
|---|---:|
| Large production receiver tread, housing and food scale | 9.9 |
| Conveyor materials, supports and machine connections | 9.9 |
| Actual two-inlet production, flow, stock, sale and camp access | 9.9 |
| Field resource and on-character cargo size/readability | 9.9 |
| Processed goods and physical cash transfer | 9.9 |
| Owl scale, silhouette and normal-camera readability | 9.9 |
| Owl anticipation, actual strike and release | 9.9 |
| Owl planted lookout and fence clearance | 9.9 |
| Native encounter retirement and conservation stress | Pass |

## Production receiver

In the normal and pinch gameplay frames, the tray and dark common roller field are broad enough to read as a major station among the existing smaller transport runs. The field model measures about 133 px tall in the matched true 2× camera. A live meal spans about 66–69 px, and the common usable tread about 120–128 px. This puts food at roughly 0.50–0.52 of the nearby adult height and the tread at 0.90–0.96, within the A16 estimate. The bold orange side shell, zinc collars, separate fork and blue ribbed cabinet carry the Havenline equipment style. The selected A16 includes a shoreline behind the tall receiver, while the tested camp keeps its own wooden customer counter. The camera can partially hide C1's legs behind this tall cabinet in some close service bearings. [A16 intake pixels](../References/A16-region-review.jpg)

Actual cooked and stored meals take distinct powered mouths, converge on the decline, and seat in separate cells on the blue cabinet. The populated view shows eight servings in four rows and two columns. The oldest serving reaches the actual buyer's hand, can be released without a player or survivor carrying freight, and creates a separate cash note on the counter. Tests verified all eight placement receipts, standstill backpressure with cabin reserve, unloaded deck draw, and all 43 paid layout and body collision checks. The receiver motion samples show the first objects roll down the common bed into the stock area and the last sale advances the paid count once. [Native intake and sale phases](Boards/Receiver-motion-phases.jpg) Physical foot routes use the clear floor outside the new shell. [Eight real warm arrivals](../Validation/Conveyor/Eight-warm.log) · [No-attendant flow](../Validation/Conveyor/Unattended-stock.log) · [Cabinet and paid layout checks](../Validation/Conveyor/DeckFinal.log)

## Resources and cash

A same-use-pose 1× and 2× comparison shows all six enlarged raw woodland/mining/material types legible as separate pickups on the snow. The quarter-view joystick run shows the six-family load supported by the pack with visible push-off and trail. At straight rear headings a full carrier still temporarily hides boots behind cargo, the same viewpoint in the previous build. Mixed prepared goods, larger green notes and individual storehouse bays are identifiable at 1×, with extra physical detail at pinch. The paid counter consumes two meals and collects two earned notes in one approach. The same two notes physically appear in the warehouse and can be retrieved by approaching the shelf. Both volume and cold revisits preserve the ledger. [Loaded-run phases](Boards/Loaded-run-phases.jpg) · [Cash comparison](Boards/Matched-cash-transfer.jpg)

## Expedition owl

The existing 130% scale and selected model remain. The fixed view now clearly separates the pale face and blue scarf, while the side and rear plumes and pack keep their original shape. Both gate seats pass. A 36-sample continuous normal-camera lookout has the same post position in every frame and its head turns smoothly through roughly 0.47 rad without moving the pack or feet. Fine amber and scarf details are easiest to see at 2×. [Continuous lookout samples](Boards/Owl-lookout-actual.jpg) · [Both gates at normal and pinch](Boards/Perch-confirmed-both-gates.jpg)

The 1× patrol shows takeoff, bank, windup, dive, actual talon impact, release and recovery. The first ordinary wolf goes from 3 to 2 at tick 79 with one owl receipt. Two outdoor bearings confirm 7 to 6 on the owl's real hit in each. The popup and bar remain beside the owl during contact and release even as an orbit hit arrives. At some 2× outdoor bearings a high early phase can momentarily pass behind the top HUD. All major phases fit the ordinary 1× gate replay, and the other outdoor crop makes the full anticipation visible. The owl uses the original swept morphed claw geometry, both named gates, and actual perimeter clearance. [Ordinary gate sequence](Boards/Owl-patrol-ordinary-1x.jpg) · [Outdoor encounter bearings](Boards/Owl-two-field-angles.jpg)

## Encounter stress and coverage

The old fixture incorrectly expected only player and survivor in the living trackers. The actual world also contains the permanent tracked stag. The corrected test verifies all three exact live identities and species and checks their surfaces during each wave. It monitors each defeated wolf and scene-node retirement, drop lifetime, duplicate loot and next-wave tracking. The 200 native timed waves pass with 572 wolves defeated out of 572 spawned, 31 alphas, peak four wolves, and zero duplicates, orphans or cleanup failures. [Exact native encounter stress](../Validation/exact/qa_encounter_waves/run.log)

Gameplay screenshots and films are native Godot using llvmpipe, 960 × 540. 1× and 2× evidence is actual fixed game camera gameplay. This scope does not add physical Fold7 or long-term 4K performance measurements.
