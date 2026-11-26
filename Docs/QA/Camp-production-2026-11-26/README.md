# Camp production inside the second expansion

The saw, meat cooker and stone drill now run inside the paid north perimeter. Enter through the south gate. The saw is behind the storehouse, the cooker is immediately to its east, and the drill is on the far side of the customer counter. The lake stays outside camp. [Play the route](Gameplay/Camp-production.mp4) · [See the gameplay camera at 1× and 2×](Gameplay/Camp-production-views.jpg)

## What the recordings show

Reference A at 00:13–00:16 connects a shoreline intake to rollers, a staffed processor and a blue-edged stock tray. At 00:38–00:43 several crop heads feed a belt to a mill just inside the fence. The fish line continues alongside it. Finished food goes to a separate counter. Reference B at 00:08, 00:10 and 00:28 shows heat and stock inside the perimeter with the customer queue outside. Havenline uses this pattern for three independent recipes. The saw makes planks, the drill makes blocks and the cooker makes roasts. Their exact locations and cycle times are Havenline playtest decisions. [Original frame comparison and sampled clips](Reference/Reference-notes.md)

## How to use the stations

- Walk to a machine's inlet with the matching material to load it. Up to four raw units fit in each inlet. The three machines can run at the same time and keep working when you leave. The saw and drill take 1.45 seconds per unit and the cooker takes 1.65 seconds. These are playtest timings.
- The rescued survivor delivers gathered wood to the storehouse. Once the second expansion opens, the survivor can also carry surplus shelf stock to its matching feeder. Materials needed for outstanding camp purchases stay available. A full feeder sends the survivor back to the shelf with the same unit.
- Finished planks and blocks stack at their own stations. Up to four roasts wait at the cooker’s opposite end. Pick one up there and carry it to the inside of the north counter to earn payment. A full cooker tray pauses the next portion. Queued goods and partial cycles survive a save and reload; production time advances during active play.

## Placement and camera

Only the last expansion gained two metres of depth. The stations unlock together at that expansion, keeping new purchase pads off the central floor. The machine guards occupy 15.68 m² of a 223.2 m² camp. The two end loading aprons are 11 m apart, and the narrow aisle behind the storehouse measures 1.65 m. An isolated in-engine collision probe 0.96 m across reached every inlet, the roast outlet, the storehouse, the counter and both gate approaches. The avatar walked through both gates in both directions.

The storehouse roof and rear wall cut away when they hide the player at the saw. On the drill exit, the foreground part of the defense tower clears the character and returns to full view when they walk away. The tower still aims and fires from its original mount. [Tower before and after](Verification/Tower-camera.jpg) · [Mechanical checks](Verification/Mechanical-QA.json)

## Build and review

All six camp-production criteria met the 9.5/10 threshold. The lowest score was 9.5 for visible material flow. One finished stone or roast is small at the default zoom. [Independent scores](Verification/Independent-review.md)

Playable source `30524e3da7906e252e1de7dd4529250b060868be`, scene `res://field_opening.tscn`, Godot 4.7.2. The replay starts from a private copy of an earned profile from the prior trial. The Linux and Android binaries are in the shared playtest download. The build instructions and all gameplay evidence are archived on the trial branch. [Try the build](Play/README.md) · [Reproduce the source](Source/README.md)
