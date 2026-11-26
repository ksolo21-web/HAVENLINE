# Mineral inventory and storage

The frozen game at `fa9d3e987859a1e46c2533f94431b4e9cae3a9e5` sends coal, slate and metal ore through separate backpack lanes and shelf bins. The reinforced storehouse opens all three mineral bays. Existing construction prices still require their original materials. Godot 4.7.2 ran the isolated tests using the normal scene `res://field_opening.tscn` after all 234 manifest entries matched the frozen source. [Reviewed source files](../Build/Reviewed-files.json)

## Previous native save

The released carry build at `e978a44b1b112bb598f9ec1724b3616ec80e6970` wrote a version-2 save in an empty temporary Linux app-data directory. Its purchase test supplied its own fixture materials, completed all eight purchases and banked the remaining resources. A fresh process running the mining build opened that save, picked up twelve unique test units using authored mineral meshes and deposited nine. A third process opened the version-3 save and rejected all three attempted duplicate pickups. Both save files below were generated entirely by these tests. [Old writer](Tests/previous-build-writer.log) · [Migration and transfers](Tests/migrate.log) · [Reopened game](Tests/reopen.log)

| Material | Before, carried / stored | After, carried / stored |
| --- | ---: | ---: |
| Wood | 0 / 13 | 0 / 13 |
| Stone | 0 / 22 | 0 / 22 |
| Meat | 0 / 28 | 0 / 28 |
| Coal | — | 1 / 2 |
| Slate | — | 1 / 3 |
| Metal ore | — | 1 / 4 |

All 91 original token IDs kept their original material, and every old receipt, amount and completion order matched. The resulting ledger has 103 tokens. Run `python verify.py` in this folder to check the original payload digests, compare both saves and recompute conservation for every material. [Generated v2 save](Fixtures/Generated-v2.json) · [Generated v3 save](Fixtures/Generated-v3.json) · [Independent checker](verify.py) · [Digest results](Fixture-verification.json)

## Inventory and presentation

The separate starter-tier regression rejected mineral deposits before the reinforced purchase. It accepted typed deposits after payment, matched the landed meshes to their bins and retained both the saved amounts and labels after another process restart. A synthetic stress test ran 120 deposits and 120 payments for each of the six materials, totaling 1,440 physical flights. It separately checked bounded presentation at one million units of each type. The mixed backpack regression assessed actual mesh bounds across 80 poses at 1× and 2× in portrait and landscape. [Starter and reinforced transitions](Tests/qa_field_minerals.log) · [High-balance shelves and receipts](Tests/qa_field_stock_limits.log) · [Mixed-load camera bounds](Tests/qa_field_pack_bounds.log) · [Atomic save checks](Tests/qa_field_save.log)

The native screenshots show the generated account above, with one coal, one slate and one metal ore carried. The high-number screenshots exercise the HUD independently by assigning a synthetic seven-digit display value to each field. This checks text layout, while the two fixture saves show the actual economy. [1280 × 720](Landscape.png) · [320 × 640](Phone.png) · [Large counters, landscape](Landscape-high.png) · [Large counters, phone](Phone-high.png)
