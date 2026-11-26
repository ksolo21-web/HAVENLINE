# Independent weapon head contact review

**9.8/10 — passed.** Four independent Godot processes exercised actual streamed pine and quarry surfaces in the shipping field scene. Starter runs used new disposable profiles. Upgraded runs opened copies of the separately earned save from the 262.617-second final touch route. Only the initial position and orientation were staged. The normal game selected the tool, advanced its rendered head and recorded the impact and resource damage. The test never called strike or supplied a hit position. [Native probe](field_rail.gd) · [Earned upgrade receipt](../Route/route-result.json)

| Tool and earned state | Offset from target center | Actual strikes | 4.50 m negative control |
|---|---:|---:|---:|
| Starter axe, one tool | 2.18 m | 3 on separate turns | 0 [record](initial-wood.log) |
| Starter pickaxe, one tool | 2.50 m | 3 on separate turns | 0 [record](initial-stone.log) |
| Upgraded axes, three tools | 3.30 m | 3 on separate turns | 0 [record](enhanced-wood.log) |
| Upgraded pickaxes, three tools | 3.30 m | 3 on separate turns | 0 [record](enhanced-stone.log) |

Both one-slot modes also spent 150 physics ticks at the upgraded 3.30 m contact distance with zero hits. The four receipts preserve the observed point, tool label, world-space direction of head travel, source ID and turn history. A separate moving touch controller registered three trunk strikes while walking and three rock strikes while running at each simulation rate. [30 Hz](moving-30.log) · [60 Hz](moving-60.log) · [120 Hz](moving-120.log)

The tests cover positive and negative range, earned versus initial state, automatic tool selection, distinct turn registration and moving contact. Exact surface reach varies with heading, mesh shape and height. The four distances above apply to the measured approaches. Visual resemblance and the weapon's clearance around the player's pack have separate reviewers. [Independent visual orbit review](../../../Orbit/README.md)
