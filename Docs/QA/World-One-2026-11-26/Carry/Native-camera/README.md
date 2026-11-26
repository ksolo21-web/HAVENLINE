# Native backpack camera comparison

The 24 repaired views use Godot’s normal gameplay camera and HUD at 1280×720 and 720×1280. Each case records the default 1× view and a full 2× pinch produced by two screen contacts. The lowest measured clearance above a visible packet was **11.3% of screen height**. All quantities remained in the typed inventory.

The same harness replayed two snapshots from the earned route with both versions of the scene. The hearth and east gate use the actor position and facing at tick 6351, with 42 wood, 9 stone and 4 meat. The northwest tier-one storehouse uses tick 7131, with 37 wood, 8 stone and 4 meat. The actor is outside, the door is open and the roof is visible. Camera, transform, progression and values matched across each pair. These are controlled scene comparisons, rendered through Mesa llvmpipe.

| Location | Landscape zoom | Previous top margin | Repaired top margin |
| --- | --- | ---: | ---: |
| East gate | 1× | −28.3% | 12.1% |
| East gate | 2× | −106.6% | 12.6% |
| Northwest house | 1× | −21.4% | 12.1% |
| Northwest house | 2× | −92.9% | 12.4% |

Negative margins put the top of the rendered load outside the viewport. The measurement projects every visible carried mesh vertex.

[Per-frame measurements and image paths](Measurements.json) · [Godot measurement harness](Measure.gd) · [Repaired east gate at full pinch](new-landscape/east-42W-9S-4M-2x.jpg) · [Repaired storehouse portrait at full pinch](new-portrait/house-37W-8S-4M-2x.jpg)
