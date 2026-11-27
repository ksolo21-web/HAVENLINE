# Paid machinery and transport

An independent gameplay reviewer scored the paid conveyor hardware and routing **9.5/10** after inspecting the normal view, the 1.78× pinch and the native cutaway. They verified 32 mobile movement checks and 1,462 sampled frames across four consecutive survivor trips. Adjacent supports can look busy at pinch, some blue drives sit in shadow, and a long guard can briefly obscure the character’s shoes. [Independent report](../Conveyors/Independent-review/Review.md) · [Reference and gameplay comparison](Gameplay-and-reference.jpg) · [Native cargo and payment](../Conveyors/Independent-review/Cargo-and-payment.jpg)

The first automation purchase sends the finished roast into the prepared-food room. The warehouse releases a serving when the counter requests one. The full purchase adds raw supply, finished-material returns and a fresh-food connection. The belt ends on the staff side of the counter. A worker still has to serve the customer.

| Purchased layout | Live freight routes | Generated straight modules | Generated quarter turns | Generated height adapters |
| --- | ---: | ---: | ---: | ---: |
| First automation | 2 | 10 | 6 | 1 |
| Expanded workshop | 8 | 24 | 13 | 3 |

The hardware uses three Meshy image-to-3D generations from the approved D01 straight, corner and incline. The generated corner needed its rollers rearranged to leave both mouths open. The expanded cooker outlet rises 0.277 m over 0.696 m. The freight follows that same incline. The gate approaches and the area surrounding the furnace stay accessible. [Meshy source images, previews and receipts](Meshy/README.md)

The normal and pinch screenshots include the final continuous snow bank on the storehouse. The freight clips were recorded before that roof edit. Each screenshot uses the normal player camera at 624 × 802 pixels. The pinch view uses 1.78× zoom. The cargo and finance team also recorded moving bundles, processed material and served food at the normal camera distance. [Documented cargo at the counter](../Conveyors/Visible-cargo-movement.jpg)

An independent reviewer drove four consecutive loaded survivor trips at 60 Hz, including storage to cooker, cooker to counter, counter to storage, and storage to saw. All arrived. The closest foot-to-guard gap was 60 mm. The player also reached the saw using the short recessed floor crossing and delivered a real wood bundle. [Four physical walks](Walkable-deliveries.json) · [Touch input and real material transfers](../Conveyors/Independent-review/Mobile-control-and-transfer.json)

Dense placements change which rail connections have room. On one legal cooker move, the plank return paused. Moving the saw and counter in the same sequence paused the wood feed. Moving the warehouse reopened all eight. The finite queues preserve ownership of the held stock. [Consecutive equipment moves](Relocated-connection-checks.json) · [Inventory and replay checks](../Conveyors/README.md)

## Comparison with the references

D01 supplies the orange guards, dark carrying face, silver support and blue coupling design. D03 shows separate warehouse utility and prepared-food ports. D05 shows a finite buffer beside the staffed, timber service counter. D06 supplies the first serial sale route and clear furnace forecourt. The supplemental Whiteout Survival footage shows material being carried to a counter and purchased roller transport supplying it around 48 and 65.50–67.25 seconds. [Approved Havenline source package](https://github.com/ksolo21-web/HAVENLINE/tree/e501bea5ed9e6f8737abb5b39799cade78b22af1/Docs/Design/ConveyorReferences/2026-11-26/connected-logistics-01) · [Video reference ledger](../References/Reference-review.md)

The D06 concept shows a fish intake, a rotated house, a lower, shorter counter feed, and a single clean view of the machinery. The existing Level 1 economy uses meat, and players can relocate the purchased equipment. The denser eight-route layout uses recessed rollers and small lifting platforms at the pedestrian crossing. A centerline clearance sweep found one 0.43 m separation between the shoulders of two cooked-food lines near the merge. The unpitched cooked serving measures 0.269 m high in the game model. Phone hardware performance and visual equivalence to the original ads remain unverified by this desktop render.
