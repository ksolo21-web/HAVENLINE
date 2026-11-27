# Survivor work pace and meal service

The independent rig critic awarded the forester’s gameplay work pace **9.5/10**. The field review followed the loaded actor for 360 physics ticks and captured 120 distinct native frames. [Critic’s field footage](../Rig-review/Forester-loaded-route.mp4) · [Independent observations](../Rig-review/Forester-observations.json)

The forester runs at up to 2.8 m/s with cargo and 3.6 m/s empty. Those limits apply to its own movement. A held meal, machine input, gathered timber or bulk material all use the loaded pace. The forester accelerates into each trip and brakes at its destination. Character 1 still has a separate 6.25 m/s maximum.

| Native route | Measured distance | Build 9 | Build 10 | Build 10 cadence at cruise |
| --- | ---: | ---: | ---: | ---: |
| Three harvested timber bundles from the pine through the south gate to the house | 15.6 m | 3.48 s | 6.20 s | 3.38 steps/s |
| Empty forester leaving the house for the stone bank | 20.3 m | 4.38 s | 6.83 s | 3.96 steps/s |

[Play the loaded timber comparison](Loaded-timber-comparison.mp4) · [Play the empty mining comparison](Empty-mining-comparison.mp4) · [Video verification](Film-receipts.json)

Both comparisons use the paid-rescue forester in `res://field_opening.tscn`, the same stationary player near the south gate and a separate disposable profile for each run. The routes finish within two centimetres of their Build 9 endpoints. Native 60 Hz samples log world and projected movement. [Matched route timing and source hashes](Matched-route-timing.json)

In the 24 fps Whiteout Survival ad, the cyan-clad worker carries a fish to the counter and runs back empty while the player stands nearby. The uninterrupted empty burst across frames 690–698 covers 6.0 projected worker heights per second. The loaded burst across 708–718 measures 5.6. Including the end of the delivery and the turn gives 2.6 across frames 700–724. Character size and camera angle affect those screen-space measurements. The slower Havenline speeds implement the requested everyday work pace. The newly recovered original of owner clip B shows the player unloading at a fence counter with customers queued outside at 7.5–9.5 seconds. Its scene makes the service action clear. The separate shot of a cyan-clad worker supplies the measurable autonomous-worker comparison. [Source, timecodes and measurements](Reference-worker-routes.json) · [Owner B footage](https://www.sprites.ai/whiteout-survival-ads/ad/1133260751579588)

At both travel speeds, the actual forester’s gloves, coat and boots use the existing rig. The stride advances with distance traveled. A full-stride contact test skins the imported boot vertices at 241 poses. Each boot has one support interval per stride. The boot rolls from heel to toe, the knee reaches 37° under load and 99° in swing, and the sole clears the floor by roughly 105 mm. [Stride, foot clearance and knee measurements](Worker-boot-and-cadence.json)

After rescue, with empty shelves and no contribution from the player, the forester paid for the first expansion and the starter storage house, then delivered harvested wood at 314.7 seconds. A mature-camp run exercised chopping, mining, saw, drill, cooker and customer service. Each of the six backpack material lanes retained its separate 500-unit capacity. [Opening build](Early-autonomous-camp.json) · [Camp jobs](jobs.json) · [Capacity](capacity.json) · [Moved stations](relocate.json)

The worker can also pick up prepared food from the physical house door. Two real cooked meals entered the prepared-food bay by conveyor. With no shoppers the worker took nothing. When the first buyer arrived, the belt reserved one meal and the worker left the remainder in stock. A second guest triggered a single worker pickup. Both customers paid once. The saved accounts balanced after the transactions. [Eight prepared-meal service checks](stored_meal.json)
