# Havenline Level 1 · Production floor · Android Build 12

[Download the Android playtest](https://havenline-level1-android-playtest.ksolo21.chatgpt.site/Build-12.apk) · [Watch the gameplay review](Play/Production-floor-playtest.mp4) · [Compare the source videos and render sheets](References/Reference-observations.md)

The independent reviewer scored unattended production **9.6/10** and the conveyor layout, stone mining, staffed ballista and furnace **9.5/10** each. These five grades cover the issues reopened by the Build 11 playtest. [Independent critique and comparison frames](References/Independent-review.md)

The signed ARM64 playtest opens `res://field_opening.tscn` from game commit `6f35a670bac57a0002aa44b9abedbb257848fd30`. The trial branch is `trial/world-one-expansion-2026-11-26`. Drag the virtual stick to move. Outside the camp, Character 1 automatically strikes nearby targets. The lower Camp and Build controls show the current purchases and placement options.

## What Alfred can test

| Area | What happens in play | Evidence |
| --- | --- | --- |
| Connected machines | Buy the machines and their connections. Wood and stone move from warehouse to processor and return as planks and blocks. The kitchen draws meat, cooks it and discharges meals. With the food line purchased, meals reach the counter even while the counter is empty. Six raw portions and one existing roast produced two ready servings and five stored meals. Seven customers subsequently paid exactly once after a restart. | [Stock and sales](Conveyors/Automation/README.md) · [Replay using signed APK resources](Verification/Signed-production-floor.json) |
| Layout and clearance | The second expansion adds a west work bay for the saw and quarry. The cooker stands by the north counter. The eight directed routes measure 54.60 m in total, with zero travel below the floor. Connected walking area in the paid camp increased from 128.56 to 183.70 m². The survivor walked all five tested routes to the working spots. | [Freight in motion](Conveyors/Paid-camp-surface-routes.mp4) · [Walk from saw to counter](Conveyors/Saw-and-counter-on-foot.mp4) · [Measured comparison](Conveyors/Surface-layout.md) |
| Quarry | Approach the exposed rock face and keep the stick still. Two strikes open seams. The third breaks the bank into four pieces and releases three collectible bundles worth 30 displayed stone. The bank returns after five seconds. The field stone, coal, slate and metal banks also passed depletion, pickup and regrowth checks. | [Gameplay recording](Stone/Mining-from-the-working-edge.mp4) · [Mining checks and source comparison](Stone/README.md) |
| Defense tower | The paid east tower carries a broad ballista on an open deck. Its visible operator tracks an exterior enemy, fires the seated bolt and reloads. A field wolf lost one HP on each of two hits. The weapon artwork used one Meshy generation costing 15 credits. | [Tower footage](Tower/Staffed-ballista-fire.mp4) · [Equipment review](Tower/README.md) · [Generation receipt](Tower/Generation.json) |
| Furnace | Buying the camp ignites the recovered stone furnace. The lower firebox and vent stay lit, smoke drifts, and returning to camp heals injury. The gate-return recording shows 23 → 26 → 29 → 30 HP. The purchased cooker handles food. | [Furnace and recovery](Furnace/Furnace-and-recovery.mp4) · [Matched reference and functional checks](Furnace/README.md) |

## Save compatibility

Three disposable Build 11 journals each went through an update and a second cold launch. Seven player-placed buildings kept their positions. One older saw placement required keeping the older cooker location for that save. A player saved in what became the west workstation returned on a reachable patch of floor. Purchases, inventory, sales and health carried over. [Migration on signed game resources](Verification/Signed-layout-migration.json) · [Reproducible fixtures](Source/Fixtures)

## Verification

The [Android package record](Verification/Android.json) records the application ID, signing certificate, version code, exact byte count and SHA-256. [The signed resource check](Verification/Signed-resource-pack.json) verified every Godot resource extracted from the APK before desktop playback. [The game manifest](Source/Reviewed-files.json) identifies the 650 reviewed source files. [The QA manifest](Source/Reviewed-QA-files.json) identifies the four test-only adjustments for bolt geometry, counter setup, purchase approaches and clearance through both gates.

All **61 native suites passed in 78 test launches**, with no reported engine errors or warnings. The complete progression passed on both the original release tests and the corrected test harness. [Native results](Verification/Reviewed-native/Native-results.json) · [QA history and reproduction](Verification/README.md)

The ordinary Level 1 progression passed 219 checks across 16 launches, including the survivor’s first claim, meals, customer payment, and a cold launch into Level 2. [Full original progression replay](Verification/Claim-recheck/Unmodified-completion/Completion-results.json)

The gameplay captures use the actual Godot gameplay camera in isolated desktop profiles. The review reel has captions and no audio track. The native audio suite checks event playback separately. Physical Galaxy Z Fold7 frame pacing, thermal behavior and 4K 60–120 FPS are unmeasured for this build.
