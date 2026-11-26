# Independent mining review

**Pass for the World One mining loop.** I reviewed `res://field_opening.tscn` at `fa9d3e987859a1e46c2533f94431b4e9cae3a9e5` on Godot 4.7.2. The four rows show stone from the opening quarry and metal ore, slate and coal from the first districts that contain them. [Gameplay comparison](Mining-camera-comparison.jpg) · [Full camera frames](Camera-originals/)

| Source | World coordinates X, Z (m) | Accepted pick contacts per depletion | Yield | Available again |
| --- | --- | --- | --- | --- |
| Stone | −6.00, 3.00 | 3 | 3 stone | 300 ticks / 5.00 s |
| Metal ore | 141.36, −5.62 | 3 | 3 metal ore | 300 ticks / 5.00 s |
| Slate | 202.07, 13.45 | 3 | 3 slate | 300 ticks / 5.00 s |
| Coal | 234.65, −7.72 | 3 | 3 coal | 300 ticks / 5.00 s |

The continuous metal-ore film shows three physical pick contacts, the three drops, the full five-second wait and a fresh strike once the bank returns. Depletion occurs at 2.90 s and the new bank becomes available at 7.90 s. The clip retains the original game mix and plays at normal speed. [Continuous gameplay film](Metal-ore-five-second-return.mp4) · [Frame and audio receipt](Metal-ore-five-second-return.json) · [Movie fixture](metal_ore_movie_fixture.gd)

The still-image fixture placed the player near each existing deposit on a fresh, isolated save. The normal orbit then selected the pickaxe and played continuously. I tested the sweep of vertices from the visible pick head against the previous frame’s deposit triangles at each of the first three contacts and the first contact after regrowth. Each exhausted deposit awarded three distinct tokens of the correct material. The tokens kept their identities through pickup and regrowth.

On all four runs the player remained within swinging reach. The bank first rose into view during the final 0.45 s. Its movement collider stayed off, and no mining hit landed during the 299 unavailable ticks. On tick 300 the full bank was visible and collidable again. A fresh pick hit followed. For the three remote sources I depleted the bank a second time and moved beyond the interaction radius. Its distant mesh disappeared during cooldown and returned at its seeded position. [Per-contact positions, frame timings, mesh checks and SHA-256 hashes](Independent-mining-physics-and-frames.json) · [Reproduction fixture](independent_mining_camera.gd)

At the 1280 × 720 gameplay camera the slate reads as a low layered slab, the metal ore shows lighter inclusions and the coal has broad dark fracture faces. The starter quarry keeps its snow cap and yields the warmer brown carried stone. The in-game source art and the approved object turnarounds are both identified in the receipt. The three new mineral deposits also have separate multi-angle close-ups. [Reference and native close-ups](Mineral-art/Reference-and-native.jpg)

This review covers the World One mineral loop. The separate Android outpost, whole-game approval and physical 4K frame rate fall outside this test.
