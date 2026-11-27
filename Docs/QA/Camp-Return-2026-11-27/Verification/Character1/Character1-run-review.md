# Character 1 running in Level 1

The previous run held both boots at opposite ends of the stride for several frames while the snow moved under the character. In the revised run, the trailing boot lifts and recovers while the leading leg accepts weight. The elbows follow a separate rhythm. The torso leans into a change in direction and the head stays closer to level.

[Watch both builds at normal speed](Character1-run-before-and-after.mp4) · [Compare the reference and both strides](Character1-reference-and-stride.jpg) · [Read the native movement measurements](Character1-run-measurements.json)

| Field measurement | Previous run | Revised run |
| --- | ---: | ---: |
| Straight travel | 7.0 m/s | 7.0 m/s |
| Longest wide split on the authored loop | 0.177 s | 0.091 s |
| Time with both boots moving under 0.45 m/s relative to the body along its path | 27% | 0% |
| Swing sole height, measured through the main scene | 8.1 cm | 12.2 cm |
| Glove travel front to back | 35.4 cm | 44.7 cm |
| Stop distance in the 60 Hz field test | 0.33 m | 0.33 m |

The wide-split measure counts an interval above 85% of that build’s own maximum front-to-back ankle separation. At the game’s 60 Hz sampling rate the revised run measured 0.100 s in that interval. During a 90° turn, the revised torso leaned 4.68° into the corner and travel speed stayed above 5.60 m/s. All twelve field movement checks passed through ordinary touch controls.

| Travel at the gameplay camera, in projected character heights/s | Whiteout reference | Level 1 at 1× | Level 1 at 2× |
| --- | ---: | ---: | ---: |
| Diagonal approach, A 12.00–12.40 s | ~3.3 | 3.64 | 3.63 |
| Lateral approach, B 13.00–13.50 s | ~4.7 | 4.52 | 4.53 |

The visible same-side boot extension in supplemental Whiteout creative 1 occurs about 0.53–0.60 s apart. The Level 1 cycle measured approximately 0.57 s. The original advertisement uses a different character and camera angle. Its visual cadence, the spacing of the actor against the ground and its compact coat silhouette guided the comparison. The exact elbow angle and turn lean are Havenline design decisions.

The film shows both builds taking the same touch input from an isolated snowfield start, turning and stopping, first at ordinary zoom and then at 2×. Each close-up comes from the gameplay frame immediately above it. The Linux Godot 4.7.2 compatibility renderer rendered each 450 × 800 gameplay view. The silent film plays at 30 fps. The measurements describe simulation and animation, and the rendering run did not measure performance on a physical phone.

Production runtime built the run. Production QA independently reviewed the selected field rig and the loaded and empty gameplay views. The asset SHA-256 is `f0d4e7fc0ac424efd23a82b9b88e47dec75d3b2de3da31281686bb338a4d43be`. Its geometry, skin weights, textures, skeleton, idle and preview locomotion clips retain their original authored data.

[Character 1 owner design, revision 7481714](https://github.com/ksolo21-web/HAVENLINE/blob/74817145ed7be6e8b9aef7eab1369d1e70112a64/Docs/Design/CharacterTurnarounds/2026-11-26/character-1-design-18617/sources/18617-original.jpg)
