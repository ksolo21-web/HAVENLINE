# Northwest storehouse

The World One build at `34df87a8195553c4636aa374ac3bfc11054a3bbd` uses one northwest storehouse and one loading apron. The starter opens the timber bay, the reinforced house adds stone, and the advanced house adds meat. The three original receipt IDs, prices and balances persist across restarts. The east expansion unlocks when all three are paid. The playable scene is `res://field_opening.tscn`. [Build manifest](../Build/Reviewed-files.json)

| Tier | Price | Earned storage |
| --- | --- | --- |
| Starter | 2 wood | Wood |
| Reinforced | 2 wood and 1 stone | Wood and stone |
| Advanced | 2 wood and 1 meat | Wood, stone and meat |

At the shared apron, enter on the left to deposit and on the right to fund the next upgrade. Leave the apron before starting a new visit. A completed upgrade keeps the gold-edged loading slate clear. The HUD gives the price or the exact stored counts. Stand inside to see the stocked bays. The foreground door can partially hide the meat quantity from the default detailed camera angle. [Loading apron](House/game-covered-loading.jpg) · [Empty interior](House/game-empty-2x.jpg) · [Stocked interior](House/game-stocked-2x.jpg) · [Shelf detail](House/game-stocked-detail.jpg) · [Reference art and image hashes](House/source-and-tests.json)

## Fresh-process checks

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

## Earned route

An independent replay checked 17,478 consecutive physics ticks from a fresh, ordinary-input run on this commit. All eight purchases completed in order. The player crossed the threshold and stayed inside for 158 physics ticks at each real house tier. All 35 wood, seven stone and three meat deposits produced individual stock changes and mixer voice starts. The full progression debited 18 wood, eight stone and two meat with matching spend cues. Every captured tick conserved collected, carried, stored and paid quantities. The independently measured route crossed both gates in both directions at all three perimeter stages and reached 100.787 m from camp. The final stock was 25 wood, one stone and three meat. This run used the normal game camera in headless mode. [Tick-by-tick audit summary and source hashes](Earned-route.json)
