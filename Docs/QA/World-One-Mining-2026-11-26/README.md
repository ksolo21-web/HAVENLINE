# Level 1 mining regrowth

The playable World One scene is `res://field_opening.tscn` at commit `fa9d3e987859a1e46c2533f94431b4e9cae3a9e5` on `trial/world-one-expansion-2026-11-26`. Stone, metal ore, coal and slate each return five seconds of play after the third successful pickaxe contact. A bank releases three units of its own material. During the final 0.45 seconds the bank becomes visible again. It accepts another hit and restores its collision at five seconds.

The continuous 8.67-second gameplay clip shows metal ore depletion, all five seconds of regrowth, and the next pick contact, with game audio. [Watch metal ore regrow](Metal-ore-five-second-return.mp4)

The gameplay comparison follows each of the four deposits from first impact through depletion and return at the normal camera. The independent reviewer also checked distant deposits as their chunks unloaded and reloaded. [Gameplay-camera comparison](Mining-camera-comparison.jpg) · [Independent review](Independent-mining-review.md)

## Where Alfred can try it

The starter stone quarry is at X −6, Z 3. From camp, travel east to find these three deposits in sequence. The X/Z coordinates are in world metres. Each deposit shares its original 3D model with its carry item, and each has its own backpack lane and storage bay. The existing reinforced storehouse purchase opens the mineral bays.

| Deposit | X | Z |
| --- | ---: | ---: |
| Metal ore | 141.36 | −5.61 |
| Slate | 202.07 | 13.45 |
| Coal | 234.65 | −7.72 |

The survey found 114 metal ore, 127 slate and 91 coal deposits. They begin outside the first 128 metres. All 34,480 previous streamed pine and stone placements retained their IDs and transforms. Steel ingots and fuel cans are separate items. [World survey](World-survey.json) · [Mineral art comparison](Mineral-art/Reference-and-native.jpg) · [Build and launch instructions](Build/README.md)

## What passed

On disposable profiles, all 82 mining assertions passed. The starter quarry and one streamed bank of each mineral returned on physics tick 300 at 60 Hz. The tests exercised partial strikes, leaving the chunk, reloading with time remaining, collecting separate drops and a second harvest. Each bank awarded exactly six distinct units across its two harvests. The scene kept counting down while the player was away in the running game. Closing the game preserved the remaining played time. [Mining checks](Mining-return.json)

A separate save migration carried all 91 original tokens and all eight receipts forward. Twelve newly earned units of coal, slate and metal ore balanced across the backpack and storehouse after restarting. [Inventory and save verification](Inventory/README.md)

All 21 native Godot suites passed on the commit above. They also cover the camp gates, progression, combat, recovery, pine regrowth, segregated storage, camera and save migration. The frozen runs returned zero engine errors or warnings. [Native results](Native-suite-results.json)

## Outstanding work and critic grade

The earlier camp film shows the furnace purchase, exterior snow and travel through both gates. [Earlier camp footage](../World-One-2026-11-26/Gameplay/World-One-Gameplay.mp4)

The previous opening received an independent 9/10 at `e978a44b1b112bb598f9ec1724b3616ec80e6970`. This mining patch has its own engineering and camera evidence. The previous grade applies to that earlier opening. [Previous critic report](../World-One-2026-11-26/Independent-review.md)

Full T01–T11 approval remains open. The production register still has active reference findings for T03, T04, T05 and T08–T11. The outstanding work includes survivor chopping, the cooker's in-game scale and phone performance, and sustained 4K 60–120 fps on physical hardware. The proposed 9.5/10 minimum was conditional on finishing that work, so the critic rules retain their existing thresholds. [Task-by-task review](../World-One-2026-11-26/Task-plan-review.md) · [Production findings](../../Production/APPROVAL_INVALIDATIONS.json)
