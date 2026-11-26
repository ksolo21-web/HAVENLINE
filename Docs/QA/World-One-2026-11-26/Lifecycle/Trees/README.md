# Tree contact and five-second return

In the Level 1 opening, each accepted axe-head intersection pushes the crown along the blade’s actual horizontal travel. Three wood splinters begin at its recorded point of contact, and four flecks of snow fall from the branches. The third accepted contact fells the pine away from the player. It reaches its full 80.8° tilt at 0.72 seconds. A completed fall starts one depletion event and produces three wood pickups.

The starter pine and a pine in the outer north-east snowfield each became harvestable exactly **300 physics ticks after depletion at 60 Hz**. The returning tree rises over the last 0.45 seconds while the target remains unavailable. Leaving and re-entering the remote pine’s chunk during recovery preserved its remaining time. Old saves containing wood timers of up to 22 seconds are capped at five on load for starter, authored grove and streamed trees. Stone retains its separate timer.

| Physics source | Game clock | Normal-clock run 1 | Normal-clock run 2 |
|---|---:|---:|---:|
| Starter pine | 5.000 s | 5.066 s | 4.997 s |
| Streamed pine | 5.000 s | 4.904 s | 5.012 s |

The normal-clock runs measured monotonic wall time between physics observations on the shared host. Both used physical axe/mesh contacts. The native screenshot pass used fixed-step time to capture the same stages. The regression suite also tested a nearby authored grove, return to its batched visual, one full three-unit yield, and preserved deposited balances of 7 wood, 4 stone and 3 meat.

[Starter sequence](starter-wood-sequence.jpg) · [Remote sequence](world1_3_-4_wood_1-sequence.jpg) · [Full starter fall](starter-wood-fall.jpg) · [Full remote fall](world1_3_-4_wood_1-fall.jpg) · [Raw measurements](tree-return-qa.json)
