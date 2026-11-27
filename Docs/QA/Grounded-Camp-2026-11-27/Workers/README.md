# Rescued survivor and north counter

Watch [the survivor serving one customer](Worker-serves-a-customer.mp4). The player walks to the inside aisle and stays outside the cashier zone. The worker arrives with the cooked roast, hands it to the first queued shopper, receives one payment and the shopper leaves. The focused silent clip runs for 1.92 seconds at 720 × 900 and 12 fps. [Counter close view](Counter-camera/03-worker-counter.jpg) · [Playback run](Counter-camera/service.json)

The survivor can hold 500 raw units of wood, stone, meat, coal, slate and metal independently. In the full-load trial every excess bundle remained on the snow. All 3,000 raw units subsequently transferred to their matching storage shelves. The worker immediately started the next paid workshop supply run. The entry for each separate kind stayed balanced across both operations. Each lane shows a bounded sample when full. The count of visible meshes per lane stayed identical at both zooms and during a turn. [Rear](500-of-each-rear.jpg) · [Moving side](500-of-each-flank-moving.jpg) · [Pinch zoom](500-of-each-pinch.jpg) · [26 checks and screen measurements](capacity.json)

| Verified in the opening scene | Evidence |
| --- | --- |
| A rescued worker physically cut a standing tree, deposited the wood, mined the western starter stone, recovered drops, supplied the paid saw, drill and cooker, then served a customer. The player stayed outside the cashier zone for the entire simulation. The final balance contained four processed wood, four processed stone, two meals cooked and one sale. | [134.85-second run and job timestamps](jobs.json) |
| The worker contributed materials to a watchtower the player had already started. Sale and construction receipts remained balanced on restore. | [Seven assistance checks](assist.json) |
| A save taken with an earned roast in the worker’s hand reopened and completed the transaction exactly once. | [Interrupted run](interrupt.json) · [Cold reload](service.json) |
| Three successive physical axe contacts, player queue/serving checks, and interrupted or full-hopper deliveries passed. | [Regression results](Regression.json) |

The local field assignment gathers timber, mines nearby stone and picks up actual loose goods from all six families. Meat comes from dropped loot. The worker's camp assignment covers a 24 m radius. Far coal, slate and metal deposits begin beyond that range. Remote mining expeditions and autonomous hunting were outside these runs.

The isolated profiles ran the native Godot opening in Linux. The customer clip uses the saved game state created by the interrupted run. [Engine, scene and source hashes](Tested-files.json) · [Reference frames, timestamps and design choices](Reference/Guide.md)
