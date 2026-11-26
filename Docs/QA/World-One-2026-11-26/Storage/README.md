# Northwest storehouse

The World One build at `e978a44b1b112bb598f9ec1724b3616ec80e6970` uses one northwest storehouse and one loading apron. The starter opens the timber bay, the reinforced house adds stone, and the advanced house adds meat. The three original receipt IDs, prices and balances persist across restarts. The east expansion unlocks when all three are paid. The playable scene is `res://field_opening.tscn`. [Build manifest](../Build/Reviewed-files.json)

| Tier | Price | Earned storage |
| --- | --- | --- |
| Starter | 2 wood | Wood |
| Reinforced | 2 wood and 1 stone | Wood and stone |
| Advanced | 2 wood and 1 meat | Wood, stone and meat |

At the shared apron, enter on the left to deposit and on the right to fund the next upgrade. Leave the apron before starting a new visit. A completed upgrade keeps the gold-edged loading slate clear. The HUD gives the price or the exact stored counts. Stand inside to see the stocked bays. The foreground door can partially hide the meat quantity from the default detailed camera angle. [Loading apron](House/game-covered-loading.jpg) · [Empty interior](House/game-empty-2x.jpg) · [Stocked interior](House/game-stocked-2x.jpg) · [Shelf detail](House/game-stocked-detail.jpg) · [Reference art and image hashes](House/source-and-tests.json)

## Carry update

The successor changed the carried-packet presentation in `field_carry.gd`. The inventory ledger, save codec, house geometry, house progression, shelf layout and prices have identical source bytes on both commits. All 720 shelf flights and the full paid scene test were rerun on the successor. [Carry and transfer evidence](../Carry/README.md)

## Earned route on e978a44b

A fresh ordinary-input run on the frozen successor recorded 17,569 physics samples with exact token conservation. The player entered all three earned interiors for 158 ticks each, crossed both gates in both directions at each of the three perimeter sizes and traveled 100.787 m from camp. The run deposited 37 wood, seven stone and three meat and paid the full progression cost of 18 wood, eight stone and two meat. A separate process recovered all eight receipts and the final balance of 27 wood, one stone and three meat in storage. [Independent headless results](Earned-route-e978a44b.json)

## Fresh-process checks on 34df87a8

Godot 4.7.2 ran each suite against 219 verified source files, using separate temporary app-data roots. The normal desktop save writer and reader ran in separate processes. [Results and SHA-256 hashes](Validation.json)

| Check | Observed result |
| --- | --- |
| Paid sequence and old accounts | All 32 ledger checks passed. A historical meat-first purchase keeps its meat permission, display tier, partial stone payment and balance. [Ledger](Tests/tiers-migration.log) |
| Shared apron | All 24 scene checks passed over 2,770 simulated ticks. Crossing the apron after purchase caused no extra debit. Visits to the former corner locations caused no deposit or purchase. [Scene](Tests/fresh-purchase.log) |
| Shelves, quantities and doors | All 30 actual-scene checks passed. A deposited unit reached its shelf and a real east-expansion payment left from the same spot and size. Entry and exit each produced one spatial door cue. [Scene](Tests/scene-shelves-audio.log) |
| High balances | 720 transfer flights landed across 120 deposits and 120 payments per material. The million-unit display probe retained one wood bundle, two stones and seven meat slices. [Transfers](Tests/stock-limits.log) · [Inventory](Tests/inventory-flight.log) |
| Restart during a purchase | A separate process reopened the house at one wood paid out of two. Standing on the apron kept that partial receipt intact. Leaving and returning spent the second unit exactly once. [Write](Tests/partial-save.log) · [Read](Tests/partial-resume.log) |
| Completed save and historical migration | Both current and historical native profiles reopened with all eight receipts and individual bays. The historical writer was the actual previous build, `1a91281d`, which bought meat, stone and then wood. A byte comparison found its old save identical after the new reader exited. [Current restart](Tests/fresh-restart.log) · [Historical writer](Tests/historical-writer.log) · [Current reader](Tests/historical-reader.log) |

The staged scene checks and the art gallery use fixtures. The ordinary-input gameplay reel records the earned route. [Gameplay](../Gameplay/)

## Earned routes on 34df87a8

The native movie covered 17,303 consecutive physics samples across 288.367 seconds with the normal game camera. All eight purchases completed in order. The player occupied the doorway interior for 158 physics ticks at each earned house tier. The film recorded 38 wood, seven stone and three meat deposits. Every deposit and each of the 18 wood, eight stone and two meat debits had a matching mixer voice start and an actual playing WAV stream. Every tick conserved collected, carried, stored and paid quantities. The route crossed both gates in both directions at each perimeter stage and reached 100.787 m from camp. A fresh process reopened the filmed save with the same eight receipts and shelves holding 28 wood, one stone and three meat. [Filmed route verification](Filmed-route.json) · [Gameplay footage](../Gameplay/)

A separate headless input run covered 17,478 ticks, visited all three earned interiors, recorded all 12 gate crossings and conserved every token. It ended with 25 wood, one stone and three meat in storage. [Independent headless results](Earned-route.json)
