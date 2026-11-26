# Character 1 equipment at Level 1 scale

The game ran from Alfred’s `alfred/character-1-final` at commit `48c6c53a0dfda117ef12c68b32cfe2b3732d5239`. The scene was `HavenlineLevel1/opening.tscn` in Godot 4.7.2, with the stock 1280 × 720 orthographic camera, size 13, offset (+7, +11, +11), and 1.75 m character height. The supplied Winter Welcome export was Option A, SHA-256 `b9b4e98ef7d27ddf5886199e3642c60c0a3bd34aa0c6520eb11e22c75718dfd0`.

The exact checkout needed one recovery mount to boot. Its furnace preload was absent from the commit, so the existing recovered furnace GLB was supplied in the disposable copy. Both T09 weapons remained byte-for-byte the same as those in the commit during their fit check.

| Run | Axe | Pickaxe | Result |
|---|---:|---:|---|
| Checked-in T09 geometry, original gameplay scale, Option A | 0.964 m | 1.086 m | Both handles intersect the glove geometry deeply. The two-handed grip fails. |
| Calibrated Meshy trial, same gameplay camera and character height | 0.950 m | 0.950 m | Both stationary two-handed holds pass the measured grip check. All ten digits are within 0.43 mm of the axe and 0.56 mm of the pickaxe across the held samples. |

The fitted trial extended only the unheld ends of the prior fitted tools to regain the intended 0.95 m length at Level 1 character scale. During motion, the largest nearest digit gap was 2.63 mm on axe and 1.69 mm on pickaxe. The game accepted one ordinary F strike per tool. In the calibrated trial the pickaxe tip still missed the actual rock. At the authored impact frame it was 0.298 m above the rock's top. Strike registration and visual contact need to agree before gameplay approval.

The default HUD footage shows the tree prompt covering the axe near the center. For the grip inspection we hid that prompt temporarily with the camera and equipment scale unchanged. The fixture runs stationary harvesting animations. The trial leaves full locomotion and carry integration unverified. No persistence was requested in any run.

## Footage

- [Checked-in equipment](/workspace/shared/downloads/Havenline/gameplay-weapons/Checked-in-Equipment.mp4)
- [Calibrated fitted Meshy trial](/workspace/shared/downloads/Havenline/gameplay-weapons/Meshy-Gameplay-Trial.mp4)
- [Side-by-side views at gameplay scale](/workspace/shared/downloads/Havenline/gameplay-weapons/Gameplay-Scale-Comparison.jpg)
- [Default HUD evidence](/workspace/shared/downloads/Havenline/gameplay-weapons/Frames/tracked-side-axe-default.png)

The [gameplay measurements](Evidence/Gameplay-Measurements.json) identify each tested model by hash and record the live equipment dimensions and resource response. The [trial folder](Trial/README.md) contains the calibrated props and the disposable test fixture.
