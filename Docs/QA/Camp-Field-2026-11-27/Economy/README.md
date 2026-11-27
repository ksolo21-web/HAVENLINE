# Warehouse, machine, and counter exchange

The implementation owner is automation and the independent visual reviewer is reference_check. The live project is `HavenlineLevel1`. Every gameplay replay here uses its ordinary `field_opening.tscn` and disposable profiles.

## Gameplay

A paid saw, quarry or cooker accepts compatible raw stock when the player approaches. Standing at the machine also collects the finished goods available on its output rack. Cargo already travelling on a purchased line remains assigned to its destination. The machines automatically feed, produce and discharge while the player is elsewhere. Before a relevant connection is purchased, the player can bring raw goods to the machine or use a rescued survivor to staff it.

Approaching the warehouse from outside stores raw resources, planks, blocks, cooked portions and cash by type. Walk through the door and stop beside a stocked shelf to take its full available contents. Wood and planks share the timber rack, stone and blocks share the masonry rack, and raw and cooked meat share the food rack. Each tray can also be selected by touching the actual stock while in reach. The cash shelf is on the right toward the back wall. Retrieved goods remain on the character while exiting, including through a restart. A later return from outside deposits them again. The working slots for autonomous shipping remain bounded, with space reserved for freight in transit. The deeper stock available for personal drop-off and the player's pack support bigger lots.

At the employee side of the serving counter, the player drops the whole carried stack of cooked portions and collects available register cash during the same visit. A sale requires an actual customer and a single prepared serving. Genuinely earned notes stay in the register until collected. Notes at the warehouse occupy the right-rear rack. The authored wood shelf's top is 0.745 m above the base. The shelf displays up to eight separated bundles while the ledger keeps the whole balance. Older profiles' already earned sales move into the warehouse on migration.

## Reference and design decisions

- Owner opening recording, paid intake, 9–16 s and 37–43 s. The installation receives stock when its player is away. The customer and staff sides follow the north counter and perimeter view in the owner D05 and D06 sheets. [Paid equipment footage](https://github.com/ksolo21-web/HAVENLINE/blob/9617201/Docs/QA/Camp-production-2026-11-26/Reference/A-paid-2fps.mp4)
- Owner source 124510, variable frame rate. The existing wood transfer read starts at frame 794, clears the pack at 795, first arrives on frames 802–804 and finishes around 820–822. The stream visibly overlaps, and unrelated stock stays on the carrier. The same cadence motivates the authored .29-second flight, with up to .55 seconds between first and last releases of a bulk stack. [Owner footage measurements](https://github.com/ksolo21-web/HAVENLINE/tree/6435e5d/HavenlineWIP/2026-11-25/transfer/wood-reference-timing)
- The service side, customer pickup, register and food buffers follow the owner counter sheet. The location of warehouse cash follows the right-rear cargo bay shown in the supplied storage cutaway. Simultaneous mass pickup, exact money denominations and the eight-bundle display limit are implementation choices. [Connected logistics sheets](https://github.com/ksolo21-web/HAVENLINE/tree/d70fbfac/Docs/Design/ConveyorReferences/2026-11-26/connected-logistics-01)

## Replay evidence

`tests/qa_personal_goods.gd` has four modes. The manual and cold modes use a paid-workshops fixture to feed all three machines, physically transfer their outputs to the house, fulfill genuine customer orders, visit the till, deposit and retrieve earned money, restart and return it. The connected mode migrates actual historical earnings and tests personal handoff with both logistic upgrades purchased and ordinary production running unattended. The bulk mode uses a deliberately constructed quantity stress case with a raw receipt for each portion, 1,207 servings and 1,021 existing sales. The visual object count is bounded independently of that quantity.

`record_exchange.gd` starts from the same paid-workshops fixture, collects six earned raw meat bundles at their interior shelf, uses the paid cooker's output and one previously finished serving to serve four real customers, and checkpoints with three further cooked portions on the player. Two passes restore that checkpoint and walk into the counter from the camp side using the gameplay camera. `record_cash_shelf.gd` uses the genuine seven-sale historical fixture and captures a single withdrawal inside the actual stockroom. Device refresh and performance are separate measurements.

## Pickup on foot

The independent reviewer scored the new walk-up shelf interaction **9.9/10**. Each 1.87-second camera replay shows the player enter the connected warehouse and collect all seven earned dollars at the rear-right shelf. Thirteen independent observations verified the untouched empty bay, single transfer into the pack, protected exit and deposit on a later visit. Four native gameplay scenarios checked all ten shelf goods, lower and upper tray selection, camera gestures, automatic shipping reservations, starter storage and cold loading. These are desktop gameplay captures at normal and 1.7× zoom. [Independent review](../References/Independent-review.md) · [Walk and custody checks](../References/Walk-up-withdrawal.json) · [Normal gameplay](Walk-to-cash-normal.mp4) · [Pinched gameplay](Walk-to-cash-pinch.mp4) · [Walkthrough checks](Shelf-walk-results.json)

The exported Android resource pack passed the same 41 checks across four separate Godot launches on desktop. The runner compared all 789 resources with the signed APK and reopened the precise cash-pickup journal for the cold launch. [Signed-pack replay](../Verification/Signed-shelf-walk.json)

## Independent counter and shelf-art review

Reference checker **reference_check** scored the transaction and warehouse-cash behavior **9.5/10** for candidate `3fad812b384335bd8ca9b5e47dc9d9557110eb4a`. At both normal zoom and 1.7×, the 2.60-second movies show 3 cooked portions moving toward the counter and 4 earned dollars moving to the character. The visible exchange spans physics ticks 50–99, or 0.82 seconds. Four separate items are visible simultaneously. The number of orders paid remains four throughout the arrival. The matched warehouse screenshot shows seven banded notes on the cash shelf and the same bare shelf after withdrawal.

[Normal camera](Counter-normal.mp4) · [Pinched camera](Counter-pinch.mp4) · [Warehouse detail](Cash-shelf-detail.png) · [Receipts and capture provenance](Economy-results.json)
