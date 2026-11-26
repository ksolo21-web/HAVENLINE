# Level 1 wolf attacks

The ridge wolf and alpha use the existing textured Havenline wolf. The previous attack moved the chest, neck and head, with no jaw bone and no animated legs in either attack clip. The revised rig splits the painted muzzle seam and weights the lower lip and jaw independently. The palate, tongue and upper canines sit inside the mouth in the resting pose.

Both wolves load their weight over their four paws, drive forward from the hind legs, reach with the forelegs, snap the jaw, land on the forequarters and tuck the hindquarters back underneath. The alpha has a longer windup, lunge and recovery. The physics clock drives the bite pose and applies damage once at closure if the target is still exposed and in reach.

| Encounter | Windup | Lunge | Authored impact | Recovery | Genuine first bite from 10.58 m |
| --- | ---: | ---: | ---: | ---: | --- |
| Ridge wolf | 0.30 s | 0.26 s | 0.170 s into lunge | 0.76 s | 3.70 s, hero 30 → 28 HP |
| Alpha | 0.45 s | 0.32 s | 0.209 s into lunge | 0.91 s | 3.68 s, hero 30 → 26 HP |

The tests observed the actual skinned jaw near 48° at maximum gape. On the first 60 Hz physics tick across contact, the regular jaw was within 5° of closed and the alpha within 6°. The 20 Hz repeats also registered exactly one contact per lunge, and the tests passed for dodging and retreating into sanctuary. All four limb chains participated. The ordinary two-wolf wave with Character 1's orbit enabled dealt real damage after 2.27 seconds.

The 32 focused rig and timing assertions are in [rig.json](Wolf-rig.json). All 34 existing world combat checks also passed in [combat.json](Wolf-combat.json).

The [side-by-side field recording](../Views/Wolf-attack-comparison.mp4) shows both ordinary wolves through impact and landing at normal speed and then at half speed. It uses 38 consecutive rendered frames per version, each sampled at 30 fps from 60 Hz field gameplay. The audio-free comparison uses the field camera with a fixed initial encounter position. The [ridge wolf](../Views/ridge-compare.jpg) and [alpha](../Views/alpha-compare.jpg) comparisons include the same four checkpoints in the new and previous rigs. The measured joint angles and contact states are in [the rig results](Wolf-rig.json). Ordinary and alpha contact both used the real field damage handler.

The source is based on field trial ee4251ae. The published earlier ordinary-wolf gameplay frame supplied the appearance reference. The original UV atlas, walk cycle, HP and bite damage are preserved. The reproducible GLB SHA-256 is 74a35c0876e6ceb8ad242225928dd6eb217444cb70e8d59648007f7bf13338ee. Physical phone performance was outside this focused body-animation check.
