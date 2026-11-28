# Havenline T06 candidate

**Independent hold at 8.8/10.** Character 1 model fidelity and the planted launch each earned 9.9/10. The playable companion role, sleeve and coat clearance, and the remaining live transition and performance evidence still hold final T06 approval. [Independent review](Review/Independent-5443762.md)

This candidate extends the approved T05 wide-receiver build. It uses the original Character 1 rig from the active beta. The selected GitHub reference renders and their hashes are recorded with the candidate. The historical Character 1 GLB in the separate `HavenlineGodot` project is also preserved. [Candidate and changed-file hashes](Candidate.json) · [Owner reference renders](Character-reference.json)

## Character 1

The first loaded boot stays planted while the other foot lifts. The launch starts the existing run cycle at the phase that matches the loaded boot. Idle, walk, run, start, release and turn evidence uses the active rig. The normal player control still requests the field run. The inclined-plane fixture exercises the same sole solver over a 10.8% grade using a test-provided surface elevation. [Six-view level gait](Motion/Level-six-views.mp4) · [Six-view incline](Motion/Incline-six-views.mp4) · [Level gameplay and directional transitions](Motion/Level-walk-run-turns.mp4)

Nine body motions cover chopping, mining, dismantling, deposit, construction, repair, rescue, service and forward attack contact. The shape of each action has separate anticipation, contact, follow-through and recovery beats. The launch reuses the field gait and the stance actions keep both foot and cuff surfaces attached. The active player receives the motion cue from successful gameplay operations. The selector also supports Character 1 as a core companion in the motion fixture. The active camp's recruit remains the original survivor, so there is no gameplay route to select Character 1 as that companion in this beta. Dismantling is a motion foundation.

The contact table records the phase and supported grip for each action. The hands interpolate through the transition without controlling damage, plot receipts, inventory or save data. [Motion checks and contact table](Validation/qa_t06_character_motion.json) · [Six-view action playback](Motion/Actions-six-views.mp4)

## Harvesting

The world census drives the payout schedule. A completed deposit yields 30 wood, 60 stone, 70 slate, 80 metal or 90 coal. The same source pays the same amount whether the player, the survivor or the snow truck harvests it. Trees and mineral banks return in five active seconds. The pre-patch stack in a saved session keeps its original receipts. [World One harvest proof](Harvest/Verification.md)

## Validation

The engine suites cover normal controls, device-shaped camera viewports, gates, transport, handoffs, combat, scarcity, regrowth and saved progress. The 200-wave stress pass includes 572 wolf defeats and 31 alphas, with zero duplicate loot and no failed cleanup cycles. The exact candidate passed 21 suites and 45 focused motion checks. The 95th percentile for a standalone action pose was 0.134 ms in the headless script. Native desktop 4K captures use the real Godot Compatibility renderer at 1× and 2×. [4K normal](Motion/4K-gameplay-1x.jpg) · [4K pinch](Motion/4K-gameplay-2x.jpg) Physical-device testing was waived by the owner. [Headless desktop comparison](Validation/Desktop-runtime-cost.json) · [Engine suites](Validation/Suites.json) · [Encounter stress output](Validation/qa_encounter_waves.json)
