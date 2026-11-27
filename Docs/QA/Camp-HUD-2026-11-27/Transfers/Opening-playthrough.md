# Opening purchase and gate playthrough

The fresh test character harvested the wood with its automatic orbit, paid for the initial camp by approaching the plot, and travelled through both gates in both directions. All 18 checks passed. The video starts on untouched snow and continues through the final safe return. [Watch the playthrough with game audio](Furnace-and-both-gates.mp4) · [Six gameplay frames](Opening-and-gate-crossings.jpg)

The first wood arrived at **20.37 s** and the game revealed the furnace and starter perimeter at **20.85 s**. The actor earned all 200 wood shown on the purchase ticket. The inventory records this as 20 bundles of 10. An empty, disposable profile and isolated settings were created for this take. Movement came through the game’s touchscreen control. [Session, position, inventory, gate and audio records](Gate.json)

| Threshold | Time in video | Corresponding gate angle | Player orbit |
|---|---:|---:|---|
| south plane out | 22.12 s | 90.0° | Active |
| south plane in | 23.42 s | 90.0° | Holstered |
| east plane out | 25.52 s | 90.0° | Active |
| east plane in | 26.83 s | 90.0° | Holstered |

Recorded from commit `989edd9283148e9f712387fb937ea36038cbd9d2`, scene `res://field_opening.tscn`, with the Build 11 HUD using the default gameplay camera at 1.00×. The native desktop renderer was llvmpipe (LLVM 19.1.7, 256 bits). Encoded viewport dimensions were 416 × 676 with 12 recorded frames per simulated second and 60 physics ticks per second. This is a desktop replay of the frozen Android export source. Device frame rate and physical Fold performance require a phone run.

The track is a stereo recording of the real game mix. Left and right channel RMS measured -23.2 and -23.2 dBFS. The field and camp music, ambient stems and individual effect timestamps are recorded alongside the threshold checks. [Audio measurements in Gate.json](Gate.json)

The first transfer and the paid camp reveal were 0.483 s apart. In the owner’s recording A, bills leave the pack at 12.6–12.9 s and the new machine starts appearing at 13.2 s. The ads use a different prop and camera, so this comparison measures the sequence and timing. [Five purchase frames](Opening-purchase-transfer.jpg) · [Timed reference observations](../../Connected-Camp-2026-11-27/References/Reference-review.md)

The old and new HUD can be compared at matching timestamps in both paid and unpaid camp states. [Matched Build 10 and Build 11 gameplay frames](Build10-and-11-HUD.jpg) · [Build 10 terminal save reloaded in Build 11](../Verification/Build10-earned-opening-loaded.json)

All 18 matched route milestones occurred at the same recorded tick in the two runs. Both finished at the same safe position with 30 HP, identical camp payments, 24 wood bundles and 3 stone bundles collected. Combat recorded one defeat and 2 meat in the Build 10 replay, compared with two defeats and 4 meat in the Build 11 replay. Separately, loading the preserved Build 10 save in Build 11 retained its original 2 meat. [Route comparison and combat counts](Gate.json) · [Existing-save verification](../Verification/Build10-earned-opening-loaded.json)
