# Character 1 in the field

The same short drag and full drag now trigger a **7.0 m/s run** in Level 1. The former 2.8 m/s loop read as a walk at the gameplay camera. The new stride loads each boot for a shorter interval, carries the body forward in flight and brings the elbow past the ribs. The head stays steadier than the upper body. Input release stops the actor in 0.33 m.

| Gameplay camera direction | Reference | Prior build | New build at 1× | New build at 2× |
| --- | ---: | ---: | ---: | ---: |
| Diagonal approach, source A 12.00–12.40 s | ~3.3 | 1.46 | 3.60 | 3.56 |
| Lateral run, source B 13.00–13.50 s | ~4.7 | 1.78 | 4.45 | 4.44 |

Values are projected Character 1 heights traveled per second. Each comparison uses a fixed ground landmark and the projected height of the moving body from hood to sole. The source advertisements vary in framing and pace. The diagonal run is about 9% faster than A and the lateral run is about 5% slower than B.

| Normal field movement | Prior build | New build |
| --- | ---: | ---: |
| Physical travel | 2.80 m/s | 7.00 m/s |
| Steps/minute | 172.9 | 210.6 |
| Same-foot cycle | 0.694 s | 0.570 s |
| Boot front-to-back travel | 0.702 m | 0.736 m |
| Forward trunk lean | 7.5° | 10.6° |

The jacket now bends cleanly under both arms across Idle, Walk, Run and FieldRun. The local fit affects 325 vertices. An independent check compared these against the whole body over 415 poses.

The field turn follows the stride as the character steers. During a planted stop the hinged boot stays within the measured ankle envelope. An eight-phase test at 120 Hz found that each 90° turn completed and each 7.0 m/s run stopped within 0.361 m. The movement fixture measured a worst sole incursion of 0.96 mm. An independent test of 442 low-boot vertices across eight additional releases measured 2.62 mm at its deepest point. A separate four-heading gameplay-camera check across 545 poses found that both former calf/boot crossings had cleared. Its largest remaining exposed boot seam measured 0.674 mm. [Native turn and braking poses](../Views/Character1-turn-and-stop.jpg)

The supplementary 30 fps reference places the same-side boot extension approximately 0.53–0.60 s apart. The new clip uses the existing fifty skin joints with a dedicated field-run cycle. The 120 Hz import preserves the rapid heel contact. The practical input regression measures the skinned sole, flight, cadence, arm action, posture, start and stop from the main field scene.

[Normal-speed before/after footage](../Views/Character1-running-comparison.mp4) · [Six-angle FieldRun poses](../Views/Character1-FieldRun-poses.jpg) · [Measured reference comparison and field results](Character1-gait.json)

The gameplay film uses the same initial position, touch direction, and 1× or 2× camera zoom in two isolated profiles. It compares the prior field trial at `73d79cb50311e1818bfb8545c60ad846c18641ef` and the reviewed Character 1 GLB `8ede1dc7d8e021d5e23dad45959a3eebe91ff3d871893fa4d683ac73d90cca09`. This locomotion film is silent.
