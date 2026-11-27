# Level 1 automated production and service

After buying the cooker, tap **Automate** inside camp. Choose **Automate meal service** for 100 wood and 60 stone, or **Connect storehouse supply** for 160 wood and 120 stone. Approach the selected floor plot to pay. Reopen **Automate** and tap the selected project to cancel it. Each project has a separate receipt. One plot appears at a time. [Portrait upgrade menu](Choose-automation.jpg) · [Selected plot](Chosen-purchase-plot.jpg)

The supply upgrade takes individual bundles from their assigned storehouse shelves. The real storehouse doors open for outgoing stock. Goods pass through the central doorway to the inputs of the purchased saw, stone processor and cooker. A later workshop joins the supply line when purchased. The meal upgrade moves finished roasts from the cooker to the north counter, where an arriving customer exchanges cash for one roast and walks away with it. Existing player and survivor deliveries can still serve an order.

[Watch automated dispatch and payment](Camp-conveyors-and-customer.mp4) · [Independent gameplay verdict](Independent-review.md)

## Playtest

Eight isolated native scene runs cover both purchase orders, a later saw purchase, rejected disk writes during transport and immediately before a customer paid, cold restarts and moving the saw with a bundle already dispatched. The original three-process touch route also completed all eleven core purchases without funding an optional line. The full test generated three planks, three stone blocks and seven paid orders from three wood, three stone, six meat and one previously cooked roast. [Receipts and individual checks](Conveyor-receipts.json)

**Rail hardware art is pending.** The in-game plots use a cut from the approved orange straight-roller turnaround. The current game renders the products on their routed journeys. The dedicated new straight rails, switches and endpoint assemblies await the owner's artwork. Rail appearance has no passing grade. [Approved straight module](Reference/Approved-straight-roller-turnaround.png)

The tested source is `0e58e8ad4ff67149dd7e61ade05f33fe08501411`, scene `res://field_opening.tscn`. [Tested file hashes](Candidate.json) The original source test uses `res://tests/qa_paid_conveyors.gd` in the Level 1 checkout. The enclosed v7 fixture was written by Build 8. It has earned buildings and food but no automation. The check uses new marked, disposable profile directories. [Historical input](Fixtures/Before-automation-v7.json)

## Reference

Recording A at 12.5–13.2 seconds shows materials paying into an upgrade and its completion reveal. At 16 seconds, goods are visible on the intake. Its 9-second frame shows the customer queue, food handoff and banknotes across the fence. The exact conveyor prices, two-portion counter rack, route speed of 3.6 metres per second and optional upgrade selection are implementation choices. [Locked recordings](https://github.com/ksolo21-web/HAVENLINE/tree/b80c61f13ba31bb0940792dd47976a8e2878dbf5/Docs/Design/ReferenceVideoLock) · [Intake at 16 seconds](Reference/A-16s-intake.jpg) · [Service at 9 seconds](Reference/A-9s-counter.jpg)
